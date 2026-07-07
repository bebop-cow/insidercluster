#!/usr/bin/env python3
"""
SQUEEZE DETECTOR · v1  (the combiner)
================================================================
Merges the two signal axes you've built:

  AXIS 1 — insider BUYING   (Form 4, code P)  → the fuse
  AXIS 2 — short POSITIONING (short float, days-to-cover) → the powder

THE THESIS:
  A short squeeze needs three things:
    1. Crowded short  (lots of shares betting it falls)
    2. Trapped shorts (high days-to-cover — can't exit fast)
    3. A catalyst     (something forcing the price up)

  An INSIDER BUYING a heavily-shorted stock is a near-perfect
  catalyst: the person who knows the company best is betting AGAINST
  the shorts with real money. If they're right, shorts cover into a
  thin float and the price rips.

  This tool finds names where AXIS 1 and AXIS 2 overlap — the setups
  neither scanner surfaces alone.

HOW IT WORKS:
  1. Run the insider scanner logic → get tickers with recent buys.
  2. For each, pull short/ownership data.
  3. Score the SQUEEZE POTENTIAL combining both axes.
  4. Rank and report.

DEPENDS ON: the parsing helpers from your insider scanner + yfinance.
Run:
  python3 squeeze_detector.py            # scan recent insider buys
  python3 squeeze_detector.py NKE RH LEU # score specific tickers
================================================================
"""

import sys
import re
import time
import math
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas requests")
    sys.exit(1)

HEADERS = {"User-Agent": "CaramelPrince Research tyrin@example.com"}


# ── AXIS 1: pull tickers with recent insider open-market buys ─────────
def recent_insider_buy_tickers(days_back=7, max_filings=100):
    """Returns {ticker: {'company':.., 'insiders':n, 'total_usd':..}}"""
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {"forms": "4", "startdt": since,
              "enddt": datetime.now().strftime("%Y-%m-%d"), "q": "purchase"}
    filings = []
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        for h in r.json().get("hits", {}).get("hits", [])[:max_filings]:
            src = h.get("_source", {})
            filings.append({"accession": h.get("_id", "").split(":")[0],
                            "ciks": src.get("ciks", [])})
    except Exception as e:
        print(f"[fetch error] {e}")
        return {}

    by_ticker = defaultdict(lambda: {"company": "?", "owners": set(),
                                     "total_usd": 0.0})
    for f in filings:
        if not f["ciks"]:
            continue
        acc = f["accession"].replace("-", "")
        cik = f["ciks"][0]
        fu = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{f['accession']}.txt"
        try:
            rr = requests.get(fu, headers=HEADERS, timeout=20)
            time.sleep(0.1)
            if rr.status_code != 200:
                continue
            t = rr.text
            tkr_m = re.search(r"<issuerTradingSymbol>(.*?)</issuerTradingSymbol>", t, re.DOTALL)
            iss_m = re.search(r"<issuerName>(.*?)</issuerName>", t, re.DOTALL)
            own_m = re.search(r"<rptOwnerCik>(.*?)</rptOwnerCik>", t, re.DOTALL)
            if not tkr_m:
                continue
            ticker = tkr_m.group(1).strip().upper()
            has_buy = False
            total = 0.0
            for block in re.findall(r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", t, re.DOTALL):
                cm = re.search(r"<transactionCode>(\w)</transactionCode>", block)
                if not cm or cm.group(1) != "P":
                    continue
                has_buy = True
                sh = re.search(r"<transactionShares>.*?<value>([\d.]+)</value>", block, re.DOTALL)
                pr = re.search(r"<transactionPricePerShare>.*?<value>([\d.]+)</value>", block, re.DOTALL)
                total += (float(sh.group(1)) if sh else 0) * (float(pr.group(1)) if pr else 0)
            if has_buy:
                d = by_ticker[ticker]
                d["company"] = iss_m.group(1).strip() if iss_m else "?"
                if own_m:
                    d["owners"].add(own_m.group(1).strip())
                d["total_usd"] += total
        except Exception:
            continue
    return by_ticker


# ── AXIS 2: short / ownership data ────────────────────────────────────
def short_data(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "short_float": info.get("shortPercentOfFloat"),   # fraction
            "short_ratio": info.get("shortRatio"),            # days to cover
            "inst_pct": info.get("heldPercentInstitutions"),
            "insider_pct": info.get("heldPercentInsiders"),
        }
    except Exception:
        return {}


# ── COMBINE: squeeze score ────────────────────────────────────────────
def squeeze_score(insider_usd, n_insiders, short_float, short_ratio):
    """
    Higher = better squeeze setup.
      · short_float and short_ratio = the powder (bigger = more fuel)
      · insider buying = the fuse (bigger $ + more insiders = stronger)
    All four must be present for a real score; missing short data → 0.
    """
    if not short_float or not short_ratio:
        return 0.0
    powder = (short_float * 100) * 2.0 + short_ratio * 3.0
    fuse = math.log10(max(insider_usd, 1)) * 2.0 + n_insiders * 4.0
    # multiplicative: need BOTH powder and fuse to score high
    return round((powder * fuse) / 100, 1)


def main():
    manual = [a.upper() for a in sys.argv[1:]]

    print("=" * 66)
    print("SQUEEZE DETECTOR · insider buying × short positioning")
    print("=" * 66)

    if manual:
        # score specific tickers — assume 1 insider, unknown $ unless scanned
        targets = {tk: {"company": tk, "owners": {"?"}, "total_usd": 100_000}
                   for tk in manual}
        print(f"Scoring {len(manual)} manual tickers "
              f"(insider $ assumed — use auto mode for real values)\n")
    else:
        print("Pulling recent insider open-market buys...\n")
        targets = recent_insider_buy_tickers()
        print(f"Found {len(targets)} tickers with insider buys.\n")

    if not targets:
        print("No insider-buy tickers found in window.")
        return

    rows = []
    for ticker, d in targets.items():
        sd = short_data(ticker)
        time.sleep(0.1)
        n_ins = len(d["owners"]) if isinstance(d["owners"], set) else 1
        score = squeeze_score(d["total_usd"], n_ins,
                              sd.get("short_float"), sd.get("short_ratio"))
        rows.append({
            "ticker": ticker, "company": d["company"][:24],
            "insiders": n_ins, "insider_usd": d["total_usd"],
            "price": sd.get("price"),
            "short_float": sd.get("short_float"),
            "short_ratio": sd.get("short_ratio"),
            "score": score,
        })

    rows.sort(key=lambda r: r["score"], reverse=True)

    print(f"{'TICKER':<7}{'SQUEEZE':<9}{'SHORT%':<8}{'D2C':<6}"
          f"{'INS':<5}{'INSIDER$':<12}COMPANY")
    print("-" * 66)
    for r in rows:
        sf = f"{r['short_float']*100:.1f}%" if r['short_float'] else "n/a"
        d2c = f"{r['short_ratio']:.1f}" if r['short_ratio'] else "n/a"
        print(f"{r['ticker']:<7}{r['score']:<9.1f}{sf:<8}{d2c:<6}"
              f"{r['insiders']:<5}${r['insider_usd']:<11,.0f}{r['company']}")

    # highlight real setups
    hot = [r for r in rows if r["score"] >= 15]
    if hot:
        print(f"\n{'='*66}\n🎯 SQUEEZE SETUPS (insider buying + crowded short)\n{'='*66}")
        for r in hot:
            print(f"\n{r['ticker']} · {r['company']} · squeeze score {r['score']}")
            print(f"   short float: {r['short_float']*100:.1f}% · "
                  f"days-to-cover: {r['short_ratio']:.1f}")
            print(f"   insider buying: ${r['insider_usd']:,.0f} "
                  f"across {r['insiders']} insider(s)")
            print(f"   → insider betting against crowded shorts. Watch for catalyst.")
    else:
        print(f"\n{'='*66}")
        print("No strong overlap setups right now. That's normal —")
        print("insider-buy + crowded-short overlap is rare, which is")
        print("exactly why it's worth catching when it appears.")

    print(f"\n{'='*66}")
    print("Short data ~2wk lagged (FINRA). Not a real-time trigger.")
    print("=" * 66)


if __name__ == "__main__":
    main()