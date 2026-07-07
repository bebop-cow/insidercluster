#!/usr/bin/env python3
"""
INSIDER CLUSTER SCANNER · v4  (the scoring build)

WHAT CHANGED FROM v3:
  v3 used a hard pass/fail: (2+ insiders AND $250k+). That threw away
  BOTH real signal types:
    · RH — 1 insider but $1.8M (a CONVICTION buy)
    · Castellum — 4 insiders but only $3k (a COORDINATION buy)
  Neither passed. Both are interesting for different reasons.

THE IDEA:
  Real quant signals aren't binary thresholds — they're continuous
  SCORES you rank and compare. We score every company on two axes:
    1. Coordination  = how many distinct insiders bought
    2. Conviction    = total dollars committed
  Combine into one score, rank, show the top N. Then you look at the
  leaderboard and judge — instead of throwing data away.

  We also TAG each signal by type so you know WHY it ranked:
    CLUSTER      = 2+ insiders (coordination-driven)
    CONVICTION   = big dollars, few insiders (money-driven)
    GOLDEN       = both (the rare NKE-style setup — the good one)

Run:
  python3 insidercluster_v4.py
  python3 insidercluster_v4.py --verbose
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
TOP_N = 10  # how many ranked signals to show

# scoring weights — tune these as you learn what predicts returns
W_INSIDERS = 10.0     # points per distinct insider
W_DOLLARS = 6.0       # points per log10(dollars)

# thresholds only for TAGGING (not filtering)
CLUSTER_MIN_INSIDERS = 2
CONVICTION_MIN_USD = 250_000

CODE_MEANING = {
    "P": "PURCHASE ← SIGNAL", "S": "sale", "A": "grant", "M": "exercise",
    "F": "tax", "G": "gift", "J": "other", "I": "other",
}


def vprint(*a):
    if VERBOSE:
        print(*a)


def fetch_recent_form4(days_back=7, max_filings=100):
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {"forms": "4", "startdt": since,
              "enddt": datetime.now().strftime("%Y-%m-%d"), "q": "purchase"}
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
    acc = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{accession}.txt"
    res = {"issuer": "?", "ticker": "?", "owner": "?", "owner_cik": cik, "buys": []}
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return res
        t = r.text
        for field, key, pat in [
            ("issuer", "issuer", r"<issuerName>(.*?)</issuerName>"),
            ("ticker", "ticker", r"<issuerTradingSymbol>(.*?)</issuerTradingSymbol>"),
            ("owner", "owner", r"<rptOwnerName>(.*?)</rptOwnerName>"),
            ("owner_cik", "owner_cik", r"<rptOwnerCik>(.*?)</rptOwnerCik>"),
        ]:
            m = re.search(pat, t, re.DOTALL)
            if m:
                res[key] = m.group(1).strip()
        for block in re.findall(
                r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>",
                t, re.DOTALL):
            cm = re.search(r"<transactionCode>(\w)</transactionCode>", block)
            if not cm or cm.group(1) != "P":
                continue
            sh = re.search(r"<transactionShares>.*?<value>([\d.]+)</value>", block, re.DOTALL)
            pr = re.search(r"<transactionPricePerShare>.*?<value>([\d.]+)</value>", block, re.DOTALL)
            dt = re.search(r"<transactionDate>.*?<value>([\d-]+)</value>", block, re.DOTALL)
            shares = float(sh.group(1)) if sh else 0
            price = float(pr.group(1)) if pr else 0
            res["buys"].append({"shares": shares, "price": price,
                                "value": shares * price,
                                "date": dt.group(1) if dt else ""})
    except Exception as e:
        vprint(f"   [parse error] {e}")
    return res


def score(n_insiders, total_usd):
    """Two-axis score. log10 on dollars so $10M isn't 40x a $250k signal."""
    dollar_pts = math.log10(max(total_usd, 1)) * W_DOLLARS
    insider_pts = n_insiders * W_INSIDERS
    return insider_pts + dollar_pts


def tag(n_insiders, total_usd):
    cluster = n_insiders >= CLUSTER_MIN_INSIDERS
    conviction = total_usd >= CONVICTION_MIN_USD
    if cluster and conviction:
        return "🥇 GOLDEN"      # NKE-style: coordinated AND big money
    if cluster:
        return "🤝 CLUSTER"     # many insiders, smaller money
    if conviction:
        return "💰 CONVICTION"  # one/few insiders, big money
    return "·  weak"


def analyze(filings):
    by_company = defaultdict(lambda: {"ticker": "?", "owners": defaultdict(list)})
    for f in filings:
        if not f["ciks"]:
            continue
        p = parse_form4(f["accession"], f["ciks"][0])
        time.sleep(0.12)
        if not p["buys"]:
            continue
        c = by_company[p["issuer"]]
        c["ticker"] = p["ticker"]
        for b in p["buys"]:
            b["owner"] = p["owner"]
            c["owners"][p["owner_cik"]].append(b)

    rows = []
    for company, data in by_company.items():
        owners = data["owners"]
        total = sum(b["value"] for lst in owners.values() for b in lst)
        n = len(owners)
        rows.append({
            "company": company, "ticker": data["ticker"],
            "insiders": n, "total": total,
            "score": score(n, total), "tag": tag(n, total),
            "owners": owners,
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def main():
    print("=" * 64)
    print("INSIDER SIGNAL SCANNER v4 · two-axis scoring")
    print(f"window={WINDOW_DAYS}d · ranking top {TOP_N} by score")
    print("=" * 64)

    filings = fetch_recent_form4()
    print(f"Pulled {len(filings)} filings.\n")
    if not filings:
        return

    rows = analyze(filings)
    if not rows:
        print("No open-market buys found in window.")
        return

    print(f"{'RANK':<5}{'SCORE':<7}{'TAG':<14}{'TICKER':<8}"
          f"{'INS':<5}{'TOTAL $':<14}COMPANY")
    print("-" * 64)
    for i, r in enumerate(rows[:TOP_N], 1):
        print(f"{i:<5}{r['score']:<7.1f}{r['tag']:<14}{r['ticker']:<8}"
              f"{r['insiders']:<5}${r['total']:<13,.0f}{r['company'][:26]}")

    # detail on anything that isn't "weak"
    strong = [r for r in rows if r["tag"] != "·  weak"]
    if strong:
        print(f"\n{'='*64}\nSIGNAL DETAIL\n{'='*64}")
        for r in strong:
            print(f"\n{r['tag']}  {r['company']} ({r['ticker']}) · "
                  f"score {r['score']:.1f}")
            print(f"   {r['insiders']} insider(s) · ${r['total']:,.0f}")
            for owner_cik, buys in r["owners"].items():
                nm = buys[0]["owner"]
                tot = sum(b["value"] for b in buys)
                print(f"     • {nm}: ${tot:,.0f}")


if __name__ == "__main__":
    main()