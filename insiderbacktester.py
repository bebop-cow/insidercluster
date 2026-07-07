#!/usr/bin/env python3
"""
INSIDER SIGNAL BACKTESTER · v1
================================================================
THE QUESTION THIS ANSWERS:
  When an insider buys on the open market, does the stock actually
  go UP afterward? And which flavor of signal works better —
  CLUSTER (many insiders) or CONVICTION (big dollars)?

  Until now every scanner just found signals. This MEASURES whether
  the signals predict returns. This is the difference between a toy
  and an edge.

HOW IT WORKS:
  1. Load a set of historical insider-buy signals (ticker + date).
  2. For each, pull the stock price on the signal date and again
     at +21, +42, +63 trading days (~1, 2, 3 months later).
  3. Compute forward returns.
  4. Compare against the SPY benchmark over the same window
     (so we measure EDGE, not just "market went up").
  5. Report win rate, average return, and edge vs benchmark —
     sliced by signal type.

WHY BENCHMARK-RELATIVE MATTERS:
  If insider buys returned +5% but SPY returned +6% over the same
  windows, the "signal" actually underperformed — it lost to just
  buying the index. Raw returns lie in a bull market. Edge = return
  minus benchmark.

DATA:
  Uses yfinance (free). On first run:
    python3 -m venv venv && source venv/bin/activate
    pip install yfinance pandas numpy

INPUT:
  A CSV of signals: ticker,date,signal_type,insiders,total_usd
  You generate this by logging your scanner output over time, OR
  seed it with the sample historical signals below to test the
  machinery immediately.
================================================================
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Run:")
    print("  pip install yfinance pandas numpy")
    sys.exit(1)

# forward windows in trading days (~21 per month)
HORIZONS = {"1mo": 21, "2mo": 42, "3mo": 63}
BENCHMARK = "SPY"


# ── SAMPLE SIGNAL SET ─────────────────────────────────────────────────
# Replace this with your own logged scanner output over time.
# Format: (ticker, signal_date, signal_type, insiders, total_usd)
# These are illustrative historical insider-buy dates to test the engine.
SAMPLE_SIGNALS = [
    ("NKE", "2026-04-13", "GOLDEN", 3, 5_026_000),   # your real trade
    ("RH",  "2026-07-01", "CONVICTION", 1, 1_832_000),
    ("CTM", "2026-07-02", "CLUSTER", 4, 2_979),
    # add more as you collect them — the more signals, the more the
    # statistics mean something. n<30 is a story, not a conclusion.
]


def flatten_columns(df):
    """
    yfinance sometimes returns MultiIndex columns like ('Close','NKE')
    even for a single ticker. Flatten to just 'Close','Open',etc.
    This is THE most common yfinance gotcha. Always do this.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def price_on_or_after(df, target_date):
    """Return the first available close on/after target_date."""
    sub = df[df.index >= target_date]
    if len(sub) == 0:
        return None
    return float(sub["Close"].iloc[0])


def price_n_days_later(df, start_date, n):
    """Close approximately n trading days after start_date."""
    sub = df[df.index >= start_date]
    if len(sub) <= n:
        return None
    return float(sub["Close"].iloc[n])


def backtest_signal(ticker, date_str, spy_df):
    """Compute forward returns for one signal, benchmark-relative."""
    try:
        start = pd.to_datetime(date_str)
        # pull a generous window after the signal
        end = start + timedelta(days=140)
        df = yf.download(ticker, start=start - timedelta(days=5),
                         end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None
        df = flatten_columns(df)
        entry = price_on_or_after(df, start)
        spy_entry = price_on_or_after(spy_df, start)
        if not entry or not spy_entry:
            return None

        row = {"ticker": ticker, "date": date_str, "entry": entry}
        for label, n in HORIZONS.items():
            exit_px = price_n_days_later(df, start, n)
            spy_exit = price_n_days_later(spy_df, start, n)
            if exit_px and spy_exit:
                stock_ret = (exit_px / entry - 1) * 100
                spy_ret = (spy_exit / spy_entry - 1) * 100
                row[f"ret_{label}"] = stock_ret
                row[f"edge_{label}"] = stock_ret - spy_ret  # THE number
            else:
                row[f"ret_{label}"] = np.nan
                row[f"edge_{label}"] = np.nan
        return row
    except Exception as e:
        print(f"   [error {ticker}] {e}")
        return None


def load_signals(path=None):
    if path:
        df = pd.read_csv(path)
        return list(df.itertuples(index=False, name=None))
    return SAMPLE_SIGNALS


def main():
    path = None
    for a in sys.argv[1:]:
        if a.endswith(".csv"):
            path = a
    signals = load_signals(path)

    print("=" * 64)
    print("INSIDER SIGNAL BACKTESTER")
    print(f"signals: {len(signals)} · horizons: {list(HORIZONS)} · "
          f"benchmark: {BENCHMARK}")
    print("=" * 64)

    if len(signals) < 30:
        print(f"\n⚠️  Only {len(signals)} signals. Results are ILLUSTRATIVE,")
        print("   not conclusive. You need ~30+ for statistics to mean")
        print("   anything, ~100+ to trust it. Keep logging scanner output.\n")

    # benchmark once
    spy_df = yf.download(BENCHMARK, start="2024-01-01",
                         end=datetime.now().strftime("%Y-%m-%d"),
                         progress=False, auto_adjust=True)
    spy_df = flatten_columns(spy_df)

    results = []
    for sig in signals:
        ticker, date_str, sigtype = sig[0], sig[1], sig[2]
        print(f"  testing {ticker} @ {date_str} ({sigtype})...")
        row = backtest_signal(ticker, date_str, spy_df)
        if row:
            row["type"] = sigtype
            results.append(row)

    if not results:
        print("\nNo results (data may be unavailable for these dates/tickers).")
        return

    rdf = pd.DataFrame(results)

    print(f"\n{'='*64}\nPER-SIGNAL RESULTS (edge = stock return − SPY return)\n{'='*64}")
    for _, r in rdf.iterrows():
        print(f"\n{r['ticker']:<6} {r['date']}  [{r['type']}]")
        for label in HORIZONS:
            ret = r.get(f"ret_{label}", np.nan)
            edge = r.get(f"edge_{label}", np.nan)
            if pd.notna(ret):
                arrow = "▲" if edge > 0 else "▼"
                print(f"    {label}: {ret:+6.1f}%  edge {edge:+6.1f}% {arrow}")

    # ── aggregate stats — the actual answer ──
    print(f"\n{'='*64}\nAGGREGATE — DOES THE SIGNAL HAVE EDGE?\n{'='*64}")
    for label in HORIZONS:
        col = f"edge_{label}"
        vals = rdf[col].dropna()
        if len(vals) == 0:
            continue
        win_rate = (vals > 0).mean() * 100
        avg_edge = vals.mean()
        print(f"\n  {label} horizon  (n={len(vals)})")
        print(f"    avg edge vs SPY : {avg_edge:+.1f}%")
        print(f"    win rate        : {win_rate:.0f}% beat the market")
        print(f"    best / worst    : {vals.max():+.1f}% / {vals.min():+.1f}%")

    # sliced by signal type
    print(f"\n{'='*64}\nBY SIGNAL TYPE (which flavor works?)\n{'='*64}")
    for sigtype in rdf["type"].unique():
        sub = rdf[rdf["type"] == sigtype]
        print(f"\n  {sigtype}  (n={len(sub)})")
        for label in HORIZONS:
            vals = sub[f"edge_{label}"].dropna()
            if len(vals):
                print(f"    {label}: avg edge {vals.mean():+.1f}% · "
                      f"win {(vals>0).mean()*100:.0f}%")

    print(f"\n{'='*64}")
    print("READING THIS: positive avg edge + win rate >50% across")
    print("horizons = the signal may have real predictive power.")
    print("Negative or ~50% = it's noise. MORE SIGNALS = more trust.")
    print("=" * 64)


if __name__ == "__main__":
    main()