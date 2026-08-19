#!/usr/bin/env python3
"""
REGIME TESTER · v2 (does fading big up-days actually pay?)
================================================================
"""

import sys
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

DEFAULT_TICKER = "SPY"
DEFAULT_THRESHOLD = 1.0        # % — "big up day" if daily return exceeds this
HISTORY_YEARS = 10
OOS_SPLIT_DATE = "2023-01-01"  # train (before) vs out-of-sample (after)


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# ── build the daily return series with a "next day return" column ─────
def build_returns(ticker, years=HISTORY_YEARS):
    """
    Downloads history and returns a DataFrame with:
      · 'ret'      = today's daily % return
      · 'next_ret' = TOMORROW's daily % return (shifted back by one)
    'next_ret' is the key trick: line up each day with what happened
    the FOLLOWING day, so we can ask "after a day like this, what came
    next?" The last row's next_ret is NaN (no tomorrow yet) — dropped.
    """
    end = pd.Timestamp.now()
    start = end - pd.DateOffset(years=years)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None
    df = flatten_columns(df)
    df = df[["Close"]].copy()
    df["ret"] = df["Close"].pct_change() * 100        # today's return %
    df["next_ret"] = df["ret"].shift(-1)              # tomorrow's return %
    df = df.dropna()
    return df


# ── label the regime: is each day a "big up day"? ─────────────────────
def is_bullish_day(ret, threshold=DEFAULT_THRESHOLD):
    """Option B: bullish if today's return exceeds the threshold."""
    return ret > threshold


# ── aggregation: given a set of next-day returns, summarize ───────────
def summarize(next_rets, label):
    """Print avg, win rate, and sample size for a set of next-day returns."""
    n = len(next_rets)
    if n == 0:
        print(f"   {label:<28} n=0 (no qualifying days)")
        return None
    avg = np.mean(next_rets)
    win = np.mean([1 if x > 0 else 0 for x in next_rets]) * 100
    print(f"   {label:<28} n={n:<5} avg next-day {avg:+.3f}%  "
          f"up {win:.0f}% of the time")
    return avg

def split_buckets(frame, threshold):
    bull_next = []
    other_next = []
    for row in frame.itertuples():
        if is_bullish_day(row.ret, threshold):
        # today was a big up day → put tomorrow's return in bull_next
            bull_next.append(row.next_ret)
        else:
        # today was not → put tomorrow's return in other_next
            other_next.append(row.next_ret)
    return bull_next, other_next

def streak_length(rets, i):
    count = 1
    j = i-1
    while j>= 0 and (rets[j] > 0) == (rets[i] > 0):
        count += 1
        j -= 1
        return count

def streak_study(df, direction="up"):
    rets = df["ret"].tolist()
    results = {}
    for i in range(len(rens) - 1):
        if (rets[i] > 0) != (direction == "up"):
            continue
        n = streak_length(rets, i)
        nxt = rets[i + 1]
        results.setdefault(n, []).append(nxt)
    return results

def print_streaks(results, direction):
    for n in sorted(results):
        vals = results[n]
        cont = sum(1 for v in vals if v > 0)
        percent = cont / len(vals) * 100 
        print(f"{direction } streak {n}:={len(vals):<5} , continued {percent:.1f}%")

def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_THRESHOLD

    df = build_returns(ticker)
    if df is None:
        print("No data.")
        return

    print(f"Loaded {len(df)} trading days.\n")

    results = streak_study(df, "up")
    print_streaks(results, "up")

    




if __name__ == "__main__":
    main()