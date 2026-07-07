#!/usr/bin/env python3
"""
SHORT INTEREST & OWNERSHIP SCANNER · v1
================================================================
A different signal axis from Form 4 buying. This looks at
POSITIONING — who's short, who's long, how crowded the trade is.

WHAT IT PULLS (per ticker, via yfinance / Yahoo — free, no key):
  · Short interest (shares sold short)
  · Short % of float  (the squeeze/pressure gauge)
  · Short ratio (days-to-cover)
  · Institutional ownership %  (hedge funds + funds)
  · Insider ownership %
  · Float and shares outstanding

HOW TO READ THE SIGNALS:
  HIGH short float (>20%)  = crowded short. Squeeze risk if catalyst hits.
  RISING short interest    = bears pressing (bearish OR squeeze fuel).
  HIGH days-to-cover (>5)  = shorts trapped if it turns.
  HIGH institutional %     = smart money owns it (validation).
  HIGH insider %           = management has skin in the game.

  The classic setup: high short float + high insider ownership +
  a positive catalyst = squeeze. (Think the meme-stock playbook,
  but grounded in the actual positioning data.)

DATA CAVEAT:
  Short interest is FINRA data, reported twice a month with ~2wk
  lag. Institutional % is quarterly 13F-derived. This is NOT
  real-time — it's positioning context, not a day-trading trigger.

Run:
  python3 short_interest_scanner.py AAPL NKE GME RH
  python3 short_interest_scanner.py            # uses default watchlist
"""

import sys
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas")
    sys.exit(1)

# your watchlist — edit freely
DEFAULT_TICKERS = ["NKE", "RH", "GME", "AMC", "CTM", "IONQ", "ASTS", "LULU"]

# thresholds for flagging (tune as you learn)
HIGH_SHORT_FLOAT = 20.0   # % — crowded short
HIGH_DAYS_COVER = 5.0     # days-to-cover — trapped shorts
HIGH_INSIDER = 10.0       # % insider ownership — skin in the game


def pct(x):
    """format a fraction (0.23) or number as a percent string."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "  n/a"
    # yfinance gives some as fraction (0.23) and some as raw %
    val = x * 100 if x < 1 else x
    return f"{val:5.1f}%"


def scan_ticker(ticker):
    """Pull positioning data for one ticker. Returns a dict."""
    try:
        t = yf.Ticker(ticker)
        info = t.info  # one network call, big dict

        short_shares = info.get("sharesShort")
        short_float = info.get("shortPercentOfFloat")       # fraction
        short_ratio = info.get("shortRatio")                # days to cover
        inst_pct = info.get("heldPercentInstitutions")      # fraction
        insider_pct = info.get("heldPercentInsiders")       # fraction
        float_shares = info.get("floatShares")
        short_prior = info.get("sharesShortPriorMonth")

        # short interest trend
        trend = None
        if short_shares and short_prior:
            trend = (short_shares - short_prior) / short_prior * 100

        return {
            "ticker": ticker,
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "short_shares": short_shares,
            "short_float": short_float,
            "short_ratio": short_ratio,
            "short_trend": trend,
            "inst_pct": inst_pct,
            "insider_pct": insider_pct,
            "float": float_shares,
        }
    except Exception as e:
        print(f"   [error {ticker}] {e}")
        return None


def flags(row):
    """Generate human-readable signal flags for a row."""
    out = []
    sf = row.get("short_float")
    if sf and sf * 100 >= HIGH_SHORT_FLOAT:
        out.append("🔥 CROWDED SHORT")
    sr = row.get("short_ratio")
    if sr and sr >= HIGH_DAYS_COVER:
        out.append("⏳ TRAPPED (high days-to-cover)")
    tr = row.get("short_trend")
    if tr is not None:
        if tr > 10:
            out.append(f"📈 shorts +{tr:.0f}% (pressing)")
        elif tr < -10:
            out.append(f"📉 shorts {tr:.0f}% (covering)")
    ip = row.get("insider_pct")
    if ip and ip * 100 >= HIGH_INSIDER:
        out.append("🤝 high insider ownership")
    # the squeeze setup
    if sf and sf * 100 >= HIGH_SHORT_FLOAT and ip and ip * 100 >= HIGH_INSIDER:
        out.append("🎯 SQUEEZE SETUP (crowded short + insider-held)")
    return out


def main():
    tickers = [a.upper() for a in sys.argv[1:]] or DEFAULT_TICKERS
    print("=" * 66)
    print("SHORT INTEREST & OWNERSHIP SCANNER")
    print(f"scanning {len(tickers)} tickers")
    print("=" * 66)

    rows = []
    for tk in tickers:
        print(f"  fetching {tk}...")
        r = scan_ticker(tk)
        if r:
            rows.append(r)

    if not rows:
        print("No data returned.")
        return

    # table
    print(f"\n{'TICKER':<7}{'PRICE':<9}{'SHORT%FLT':<10}"
          f"{'DAYS2CVR':<10}{'INST%':<8}{'INSIDER%':<9}")
    print("-" * 66)
    for r in rows:
        print(f"{r['ticker']:<7}"
              f"${str(round(r['price'],2)) if r['price'] else 'n/a':<8}"
              f"{pct(r['short_float']):<10}"
              f"{str(round(r['short_ratio'],1)) if r['short_ratio'] else 'n/a':<10}"
              f"{pct(r['inst_pct']):<8}"
              f"{pct(r['insider_pct']):<9}")

    # flags
    print(f"\n{'='*66}\nSIGNAL FLAGS\n{'='*66}")
    any_flag = False
    for r in rows:
        f = flags(r)
        if f:
            any_flag = True
            print(f"\n{r['ticker']}  (${round(r['price'],2) if r['price'] else 'n/a'})")
            for flag in f:
                print(f"   {flag}")
    if not any_flag:
        print("No notable positioning flags in this set.")

    print(f"\n{'='*66}")
    print("Short interest = FINRA, ~2wk lag. Institutional = 13F quarterly.")
    print("This is positioning CONTEXT, not a real-time trigger.")
    print("=" * 66)


if __name__ == "__main__":
    main()