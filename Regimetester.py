#!/usr/bin/env python3
"""
REGIME TESTER · v1  (does fading big up-days actually pay?)
================================================================
THE HYPOTHESIS (yours):
  "If the market had a big bullish day, take puts the next day —
   the contradiction is profitable."

  That's a bet on MEAN REVERSION: a big up day is followed by a
  down day often enough to profit from fading it.

THE HONEST DEFAULT EXPECTATION:
  For broad indices this usually does NOT work — markets drift up,
  and daily reversion at the index level is mostly arbitraged away.
  The most likely finding is "no edge" or "slight momentum."
  We are NOT assuming the answer. We MEASURE it and let the data
  tell us: FADE it, GO WITH it, or NO EDGE.

DEFINITION OF "BULLISH TODAY" (Option B):
  today's return > THRESHOLD  (default +1%)

WHAT WE MEASURE:
  For every historical day that was "bullish" by that definition,
  record the NEXT day's return. Then:
    · average next-day return after big up days
    · win rate (how often next day was UP)
  Compare against:
    · the baseline (avg next-day return across ALL days)
    · days that were NOT big-up (everything else)

  Verdict logic:
    next-day avg clearly NEGATIVE → fading works (buy puts) → your thesis
    next-day avg clearly POSITIVE → momentum works (buy calls)
    next-day avg ≈ baseline       → NO EDGE (don't trade it)

HONEST TESTING GUARDRAILS (built in):
  · OUT-OF-SAMPLE split: find the pattern on older data, confirm it
    still holds on newer data. A pattern only in one slice = noise.
  · We report sample size — need hundreds+ of qualifying days.
  · Transaction costs aren't modeled here; a tiny edge is not real
    after costs. Keep that in mind reading the output.

DATA: yfinance, SPY, multi-year daily history.

Run:
  python3 regime_tester.py
  python3 regime_tester.py SPY 1.5      # ticker, threshold %
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


# ══════════════════════════════════════════════════════════════════════
# MAIN — WE BUILD THIS TOGETHER. Skeleton below; you fill the logic.
# ══════════════════════════════════════════════════════════════════════
def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_THRESHOLD

    print("=" * 60)
    print(f"REGIME TESTER · {ticker} · 'big up day' = return > {threshold}%")
    print("=" * 60)

    df = build_returns(ticker)
    if df is None:
        print("No data.")
        return

    print(f"Loaded {len(df)} trading days.\n")

    # ---- STEP 1: split the data into two buckets ---------------------
    # For every day, we know today's 'ret' and tomorrow's 'next_ret'.
    # We want to separate the next-day returns into:
    #   · bull_next  = next_ret for days that WERE big up days
    #   · other_next = next_ret for days that were NOT
    #
    # HINT: loop over df.itertuples() (or use boolean masks). For each
    # row, test is_bullish_day(row.ret, threshold). Put row.next_ret in
    # the right bucket.
    #
    # TODO (you): build bull_next and other_next as two lists.

    
    bull_next, other_next = split_buckets(df, threshold)

    # ---- STEP 2: also compute the baseline ---------------------------
    # baseline = ALL next-day returns, regardless of regime.
    # TODO (you): one line — the whole 'next_ret' column as a list.
    all_next = df["next_ret"].tolist()  # replace

    # ---- STEP 3: summarize and compare -------------------------------
    print("FULL SAMPLE:")
    # TODO (you): call summarize() on all three buckets with labels like
    #   "after big UP day", "after other days", "baseline (all days)"
    summarize(bull_next, "after big UP day")
    summarize(other_next, "after other days")
    summarize(all_next, "baseline(all days)")

    # ---- STEP 4: OUT-OF-SAMPLE check ---------------------------------
    # Split df at OOS_SPLIT_DATE. Repeat the big-up-day analysis on the
    # 'before' slice and the 'after' slice SEPARATELY. If fading only
    # works in one slice, it's noise, not edge.
    before = df[df.index < OOS_SPLIT_DATE]
    after  = df[df.index >= OOS_SPLIT_DATE]
    
    before_bull, before_other = split_buckets(before, threshold)
    summarize(before_bull, "big UP day [2015-2022]")

    after_bull, after_other = split_buckets(after, threshold)
    summarize(after_bull, "big UP day [2023-2026]")
    




if __name__ == "__main__":
    main()