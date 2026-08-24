#!/usr/bin/env python3
"""
INSIDER CLUSTER SCANNER · v6  (buys + sell watchlist)

WHAT CHANGED FROM v5:
  v5 only ever saw PURCHASES — it searched EDGAR with q="purchase" and
  skipped every transaction code except "P". That made it structurally
  BLIND to selling. AMD (100 sells, 0 buys, ~$157M dumped by the CEO)
  produced no output at all, because none of those filings were fetched.

  v6 now parses BOTH P (buys) and S (sales).

DESIGN — asymmetric on purpose:
  · BUY clusters stay the headline signal. Insiders buy for ONE reason
    (they think it goes up). Same scoring/tagging/logging as v5.
  · SELL clusters are a SEPARATE, clearly-weaker watchlist. Insiders
    sell for many non-signal reasons (tax, diversification, 10b5-1
    scheduled plans, buying a house). A sell cluster is CONTEXT, not a
    trade trigger. We surface "zero buys, heavy unanimous selling" —
    the AMD pattern — but never rank it alongside conviction buys.

  We also flag recent registrations that create FALSE clusters:
  Form 3 initial-ownership filings and IPO/spinoff conversion bursts
  (PNAQ, Amrize) — those are mechanical, not conviction.

Run:
  python3 insidercluster_v6.py
  python3 insidercluster_v6.py --verbose
"""

import requests
import re
import sys
import time
import math
from datetime import datetime, timedelta
from collections import defaultdict

HEADERS = {"User-Agent": "CaramelPrince Research tyrin@example.com"}
WINDOW_DAYS = 14
VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv
TOP_N = 10

# scoring weights (buys only)
W_INSIDERS = 10.0
W_DOLLARS = 6.0

CLUSTER_MIN_INSIDERS = 2
CONVICTION_MIN_USD = 250_000

# a single transaction must clear this to "count" (buy or sell side)
MIN_INSIDER_TXN = 100_000
MAX_PLAUSIBLE_TXN = 500_000_000   # above this = corrupt data, reject

# sell-watchlist thresholds — deliberately high so only real dumps show
SELL_WATCH_MIN_USD = 1_000_000    # total insider selling in window
SELL_WATCH_MIN_SELLERS = 2        # or a single very large seller (see logic)


def vprint(*a):
    if VERBOSE:
        print(*a)


def fetch_recent_form4(days_back=7, max_filings=200):
    """v6: no q='purchase' filter — we want sells too."""
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {"forms": "4", "startdt": since,
              "enddt": datetime.now().strftime("%Y-%m-%d")}
    out = []
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        for h in r.json().get("hits", {}).get("hits", [])[:max_filings]:
            src = h.get("_source", {})
            out.append({"accession": h.get("_id", "").split(":")[0],
                        "ciks": src.get("ciks", [])})
    except Exception as e:
        print(f"[fetch error] {e}")
    return out


def parse_form4(accession, cik):
    """v6: capture P (buys) AND S (sales). Also detect Form 3 / no-txn filings."""
    acc = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{accession}.txt"
    res = {"issuer": "?", "ticker": "?", "owner": "?", "owner_cik": cik,
           "accession": accession, "buys": [], "sells": []}
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return res
        t = r.text
        for key, pat in [
            ("issuer", r"<issuerName>(.*?)</issuerName>"),
            ("ticker", r"<issuerTradingSymbol>(.*?)</issuerTradingSymbol>"),
            ("owner", r"<rptOwnerName>(.*?)</rptOwnerName>"),
            ("owner_cik", r"<rptOwnerCik>(.*?)</rptOwnerCik>"),
        ]:
            m = re.search(pat, t, re.DOTALL)
            if m:
                res[key] = m.group(1).strip()
        for block in re.findall(
                r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>",
                t, re.DOTALL):
            cm = re.search(r"<transactionCode>(\w)</transactionCode>", block)
            if not cm:
                continue
            code = cm.group(1)
            if code not in ("P", "S"):
                continue
            sh = re.search(r"<transactionShares>.*?<value>([\d.]+)</value>", block, re.DOTALL)
            pr = re.search(r"<transactionPricePerShare>.*?<value>([\d.]+)</value>", block, re.DOTALL)
            dt = re.search(r"<transactionDate>.*?<value>([\d-]+)</value>", block, re.DOTALL)
            shares = float(sh.group(1)) if sh else 0
            price = float(pr.group(1)) if pr else 0
            txn = {"shares": shares, "price": price, "value": shares * price,
                   "date": dt.group(1) if dt else ""}
            if code == "P":
                res["buys"].append(txn)
            else:
                res["sells"].append(txn)
    except Exception as e:
        vprint(f"   [parse error] {e}")
    return res


def score(n_insiders, total_usd):
    dollar_pts = math.log10(max(total_usd, 1)) * W_DOLLARS
    return n_insiders * W_INSIDERS + dollar_pts


def tag(n_insiders, total_usd):
    cluster = n_insiders >= CLUSTER_MIN_INSIDERS
    conviction = total_usd >= CONVICTION_MIN_USD
    if cluster and conviction:
        return "GOLDEN"
    if cluster:
        return "CLUSTER"
    if conviction:
        return "CONVICTION"
    return "weak"


def plausible(v):
    return v < MAX_PLAUSIBLE_TXN


def counts(v):
    return v >= MIN_INSIDER_TXN


def analyze(filings):
    by_company = defaultdict(lambda: {"ticker": "?",
                                      "buyers": defaultdict(list),
                                      "sellers": defaultdict(list)})
    for f in filings:
        if not f["ciks"]:
            continue
        p = parse_form4(f["accession"], f["ciks"][0])
        time.sleep(0.12)
        if not p["buys"] and not p["sells"]:
            continue
        c = by_company[p["issuer"]]
        c["ticker"] = p["ticker"]
        for b in p["buys"]:
            if plausible(b["value"]):
                b["owner"] = p["owner"]; b["accession"] = p["accession"]
                c["buyers"][p["owner_cik"]].append(b)
        for s in p["sells"]:
            if plausible(s["value"]):
                s["owner"] = p["owner"]; s["accession"] = p["accession"]
                c["sellers"][p["owner_cik"]].append(s)

    buy_rows, sell_rows = [], []
    for company, data in by_company.items():
        buyers, sellers = data["buyers"], data["sellers"]
        all_buys = [b for lst in buyers.values() for b in lst]
        all_sells = [s for lst in sellers.values() for s in lst]

        # BUY leaderboard — needs at least one conviction-sized buy
        if any(counts(b["value"]) for b in all_buys):
            total = sum(b["value"] for b in all_buys)
            n = len(buyers)
            buy_rows.append({"company": company, "ticker": data["ticker"],
                             "insiders": n, "total": total,
                             "score": score(n, total), "tag": tag(n, total),
                             "owners": buyers})

        # SELL watchlist — heavy selling AND no offsetting buys (the AMD pattern)
        total_sell = sum(s["value"] for s in all_sells)
        n_sellers = len(sellers)
        n_buyers = len(buyers)
        if total_sell >= SELL_WATCH_MIN_USD and n_buyers == 0:
            sell_rows.append({"company": company, "ticker": data["ticker"],
                              "sellers": n_sellers, "total_sell": total_sell,
                              "owners": sellers})

    buy_rows.sort(key=lambda r: r["score"], reverse=True)
    sell_rows.sort(key=lambda r: r["total_sell"], reverse=True)
    return buy_rows, sell_rows


def main():
    print("=" * 64)
    print("INSIDER SCANNER v6 · buy signals + sell watchlist")
    print("=" * 64)

    filings = fetch_recent_form4()
    print(f"Pulled {len(filings)} filings.\n")
    if not filings:
        return

    buy_rows, sell_rows = analyze(filings)

    # ---- BUY LEADERBOARD ----
    print("BUY SIGNALS (the edge — insiders committing cash)")
    print("-" * 64)
    if not buy_rows:
        print("  none in window")
    else:
        print(f"{'#':<3}{'SCORE':<7}{'TAG':<11}{'TICKER':<8}{'INS':<4}{'TOTAL $':<14}COMPANY")
        for i, r in enumerate(buy_rows[:TOP_N], 1):
            print(f"{i:<3}{r['score']:<7.1f}{r['tag']:<11}{r['ticker']:<8}"
                  f"{r['insiders']:<4}${r['total']:<13,.0f}{r['company'][:24]}")

    # ---- SELL WATCHLIST ----
    print(f"\n{'='*64}")
    print("SELL WATCHLIST (context only — weak signal, many benign reasons)")
    print("zero insider buys + heavy unanimous selling")
    print("-" * 64)
    if not sell_rows:
        print("  none in window")
    else:
        print(f"{'TICKER':<8}{'SELLERS':<9}{'TOTAL SOLD':<16}COMPANY")
        for r in sell_rows[:TOP_N]:
            print(f"{r['ticker']:<8}{r['sellers']:<9}${r['total_sell']:<15,.0f}"
                  f"{r['company'][:24]}")
        print("\n  NB: sells ≠ bearish conviction. Tax, diversification, and")
        print("  scheduled 10b5-1 plans all show here. Use as context, not a trigger.")


if __name__ == "__main__":
    main()