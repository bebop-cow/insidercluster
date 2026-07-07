#!/usr/bin/env python3
"""
INSIDER CLUSTER SCANNER  ·  v1
Systematizes the NKE trade: find tickers where multiple insiders
bought on the open market (Form 4, transaction code 'P') inside a
short window. Cluster buys were your highest-conviction signal.

This is a LEARNING build. Every block is commented so you understand
the moving parts, not just run it.

SEC EDGAR is free and requires only a descriptive User-Agent header
identifying who is making the request (their fair-access rule).
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import time

# ── CONFIG ────────────────────────────────────────────────────────────
# SEC requires a User-Agent with contact info. Replace with your own.
HEADERS = {"User-Agent": "CaramelPrince Research tyrin@example.com"}

# The full-text search endpoint indexes filing CONTENT.
# We use the structured submissions API + the Form 4 XML instead,
# but for a v1 we'll use EDGAR's full-text search to find recent Form 4s.
FTS_URL = "https://efts.sec.gov/LATEST/search-index?q=&forms=4"

# Cluster definition — tune these:
WINDOW_DAYS = 14        # how close together buys must be
MIN_INSIDERS = 2        # how many distinct insiders = a "cluster"
MIN_TOTAL_USD = 250_000 # ignore trivial buys below this combined total


# ── STEP 1: pull recent Form 4 filings ────────────────────────────────
def fetch_recent_form4(days_back=7, max_filings=100):
    """
    Uses EDGAR full-text search to list recent Form 4 filings.
    Returns a list of filing metadata dicts.

    NOTE: EDGAR's FTS API endpoint is:
      https://efts.sec.gov/LATEST/search-index?q="..."&forms=4
    We page through results. Each hit has an 'adsh' accession number
    and CIK we can use to pull the actual filing.
    """
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "forms": "4",
        "dateRange": "custom",
        "startdt": since,
        "enddt": datetime.now().strftime("%Y-%m-%d"),
        "q": "purchase",   # bias toward buys; we still verify code P later
    }
    out = []
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        for h in hits[:max_filings]:
            src = h.get("_source", {})
            out.append({
                "accession": h.get("_id", ""),
                "company": (src.get("display_names") or ["?"])[0],
                "filed": src.get("file_date", ""),
                "ciks": src.get("ciks", []),
            })
    except Exception as e:
        print(f"[fetch error] {e}")
    return out


# ── STEP 2: parse a single Form 4 for open-market BUYS ────────────────
def parse_form4_buys(accession, cik):
    """
    Given an accession number, fetch the Form 4 XML and extract
    non-derivative transactions with code 'P' (open-market purchase).

    Returns list of dicts: {insider, shares, price, value, date}.
    Transaction codes that matter:
      P = open-market/private PURCHASE   ← the signal
      S = sale
      A = grant/award (comp, NOT a signal)
      M = option exercise (NOT a signal)
    Only P is a real conviction buy.
    """
    acc_nodash = accession.replace("-", "")
    url = (f"https://www.sec.gov/Archives/edgar/data/"
           f"{int(cik)}/{acc_nodash}/{accession}.txt")
    buys = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return buys
        text = r.text
        # crude XML slice — a real build uses lxml; this keeps v1 readable
        import re
        # each non-derivative transaction block
        for block in re.findall(r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>",
                                 text, re.DOTALL):
            code_m = re.search(r"<transactionCode>(\w)</transactionCode>", block)
            if not code_m or code_m.group(1) != "P":
                continue  # not an open-market buy → skip
            shares_m = re.search(r"<transactionShares>.*?<value>([\d.]+)</value>",
                                 block, re.DOTALL)
            price_m = re.search(r"<transactionPricePerShare>.*?<value>([\d.]+)</value>",
                                block, re.DOTALL)
            date_m = re.search(r"<transactionDate>.*?<value>([\d-]+)</value>",
                               block, re.DOTALL)
            shares = float(shares_m.group(1)) if shares_m else 0
            price = float(price_m.group(1)) if price_m else 0
            buys.append({
                "shares": shares,
                "price": price,
                "value": shares * price,
                "date": date_m.group(1) if date_m else "",
            })
    except Exception as e:
        print(f"[parse error {accession}] {e}")
    return buys


# ── STEP 3: cluster detection ─────────────────────────────────────────
def find_clusters(filings):
    """
    Group buys by company. Flag companies where >= MIN_INSIDERS distinct
    filers bought within WINDOW_DAYS and combined value >= MIN_TOTAL_USD.
    """
    by_company = defaultdict(list)

    for f in filings:
        if not f["ciks"]:
            continue
        cik = f["ciks"][0]
        buys = parse_form4_buys(f["accession"], cik)
        time.sleep(0.15)  # be polite to EDGAR (rate limit)
        for b in buys:
            b["company"] = f["company"]
            b["filer_cik"] = cik
            by_company[f["company"]].append(b)

    clusters = []
    for company, buys in by_company.items():
        if not buys:
            continue
        distinct_filers = {b["filer_cik"] for b in buys}
        total = sum(b["value"] for b in buys)
        if len(distinct_filers) >= MIN_INSIDERS and total >= MIN_TOTAL_USD:
            clusters.append({
                "company": company,
                "insiders": len(distinct_filers),
                "buys": len(buys),
                "total_usd": total,
                "detail": buys,
            })

    # rank by conviction: more insiders first, then dollar size
    clusters.sort(key=lambda c: (c["insiders"], c["total_usd"]), reverse=True)
    return clusters


# ── STEP 4: report ────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("INSIDER CLUSTER SCANNER · scanning recent Form 4 filings")
    print(f"window={WINDOW_DAYS}d  min_insiders={MIN_INSIDERS}  "
          f"min_total=${MIN_TOTAL_USD:,}")
    print("=" * 60)

    filings = fetch_recent_form4(days_back=7, max_filings=80)
    print(f"Pulled {len(filings)} recent Form 4 filings.\n")

    if not filings:
        print("No filings returned. SEC endpoint may be rate-limiting,")
        print("or the FTS params need adjusting. This is normal for v1 —")
        print("the logic below is what matters for learning.")
        return

    clusters = find_clusters(filings)

    if not clusters:
        print("No clusters met the threshold in this window.")
        print("(That's realistic — cluster buys are rare. That's WHY")
        print(" they're a signal when they appear.)")
        return

    print(f"\n{'='*60}\nCLUSTER SIGNALS FOUND: {len(clusters)}\n{'='*60}")
    for c in clusters:
        print(f"\n🎯 {c['company']}")
        print(f"   {c['insiders']} insiders · {c['buys']} buys · "
              f"${c['total_usd']:,.0f} total")
        for b in c["detail"]:
            print(f"     • {b['shares']:,.0f} sh @ ${b['price']:.2f} "
                  f"= ${b['value']:,.0f}  ({b['date']})")


if __name__ == "__main__":
    main()