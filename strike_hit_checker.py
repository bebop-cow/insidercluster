#!/usr/bin/env python3
"""
STRIKE HIT CHECKER · v2
================================================================
THE QUESTION:
  For every option position you actually traded, if you had instead
  bought a LONGER-DATED contract (3mo or 6mo out from your ORIGINAL
  entry date) at the SAME strike, would the stock ever have reached
  that strike before the longer expiry?

  This tests your DIRECTIONAL READ in isolation, separate from the
  DTE mistake. If most of these say YES, it means: your thesis was
  usually right, you just didn't give it time. If most say NO, your
  directional reads were the problem all along, and more time
  wouldn't have saved you.

DEFINITION OF "HIT" (Option A - the default, simplest to build):
  For a CALL: the stock's daily CLOSE reached or exceeded the strike
              on at least one day between entry and the window end.
  For a PUT:  the stock's daily CLOSE reached or fell below the
              strike on at least one day in that window.

  This uses daily closes, not intraday highs/lows. A stock that
  spiked above the strike intraday but closed below it every day
  would show as "No" here. That's a deliberate simplification -
  Option C below is the harder, more precise version.

  (Alternative — Option C, intraday touch: use the daily HIGH for
  calls / daily LOW for puts instead of Close. Catches a wick above
  the strike that never closed there. More "true" but needs the
  High/Low columns, which this skeleton already pulls, so it's a
  small change to make later if Option A feels too strict.)

INPUT:
  Your trade CSV. Each row is one option leg. We de-duplicate to
  one row per (ticker, entry_date, strike, call/put) — since a
  single position often has multiple BTO/STC legs, we only need the
  ORIGINAL entry date and strike, not every leg.

OUTPUT:
  A CSV: ticker, cp, strike, entry_date, entry_price,
         window_3mo_end, hit_in_3mo (Y/N), date_hit_3mo,
         window_6mo_end, hit_in_6mo (Y/N), date_hit_6mo

Run:
  python3 strike_hit_checker.py trades.csv
================================================================
"""

import sys
import re
import pandas as pd
import numpy as np
from datetime import timedelta

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)


def flatten_columns(df):
    """The yfinance MultiIndex gotcha - you know this one."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def load_and_dedupe_positions(csv_path):
    """
    Reads the raw Robinhood-style CSV and collapses it down to ONE
    row per distinct position: (ticker, call/put, strike, entry_date).

    A single position usually has several rows (BTO to open, maybe
    more BTO/STC/BTC legs). We only care about the FIRST entry date
    and the strike - not the exits, not the P&L. This function does
    the same Description-parsing you've already built in every other
    script (the ticker/expiry/call-put/strike regex).

    Returns a DataFrame with columns: ticker, cp, strike, entry_date
    """
    df = pd.read_csv(csv_path, skipfooter=2, engine="python")

    def money(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip().replace("$", "").replace(",", "")
        neg = s.startswith("(")
        s = s.strip("()")
        if s == "":
            return np.nan
        v = float(s)
        return -v if neg else v

    df["amt"] = df["Amount"].apply(money)
    df["date"] = pd.to_datetime(df["Activity Date"], format="%m/%d/%Y")

    pat = re.compile(r"^(\S+)\s+(\d+/\d+/\d+)\s+(Call|Put)\s+\$([\d,.]+)$")

    def parse(d):
        m = pat.match(str(d).strip())
        if not m:
            return pd.Series([None, None, None, None])
        return pd.Series([m.group(1), m.group(2), m.group(3),
                          float(m.group(4).replace(",", ""))])

    df[["ticker", "exp", "cp", "strike"]] = df["Description"].apply(parse)
    df = df[df["ticker"].notna()]

    # keep only the OPENING legs (BTO/STO) - that's the entry date/price
    opens = df[df["Trans Code"].isin(["BTO", "STO"])].copy()

    opens = opens.sort_values("date")
    positions = opens.groupby(["ticker", "cp", "strike"]).first().reset_index()
    positions = positions.rename(columns={"date": "entry_date", "price": "entry_price"})
    return positions


def get_price_history(ticker, start_date, end_date):
    """
    Pulls daily price history for one ticker, from start_date to
    end_date (with a small buffer on each side). Returns a DataFrame
    with Close, High, Low - already flattened.
    """
    try:
        df = yf.download(ticker,
                         start=(start_date - timedelta(days=3)).strftime("%Y-%m-%d"),
                         end=(end_date + timedelta(days=3)).strftime("%Y-%m-%d"),
                         progress=False)
        if df.empty:
            return None
        return flatten_columns(df)
    except Exception as e:
        print(f"   [error fetching {ticker}] {e}")
        return None


def check_hit(price_df, entry_date, window_end, strike, cp):
    """
    Given a ticker's price history, checks whether the CLOSE reached
    the strike (in the right direction for call vs put) at any point
    between entry_date and window_end.

    Returns (hit: bool, date_hit: str or None)
    """
    # slice the window
    window = price_df[(price_df.index >= entry_date) &
                      (price_df.index <= window_end)]
    if window.empty:
        return False, None, None

    if cp == "Call":
        matches = window[window["Close"] >= strike]
    else:  # Put
        matches = window[window["Close"] <= strike]

    if len(matches) > 0:
        hit_date = matches.index[0]
        days = (hit_date - entry_date).days
        return True, hit_date.strftime("%Y-%m-%d"), days

    return False, None, None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 strike_hit_checker.py <your_trades.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    print("=" * 64)
    print("STRIKE HIT CHECKER")
    print("=" * 64)

    positions = load_and_dedupe_positions(csv_path)
    print(f"Distinct positions found: {len(positions)}\n")

    results = []
    for i, pos in positions.iterrows():
        ticker = pos["ticker"]
        cp = pos["cp"]
        strike = pos["strike"]
        entry_date = pos["entry_date"]

        window_3mo_end = entry_date + timedelta(days=91)
        window_6mo_end = entry_date + timedelta(days=182)

        print(f"  checking {ticker} {cp} ${strike} (entry {entry_date.date()})...")

        price_df = get_price_history(ticker, entry_date, window_6mo_end)
        if price_df is None:
            results.append({
                "ticker": ticker, "cp": cp, "strike": strike,
                "entry_date": entry_date.date(),
                "hit_in_3mo": "no data", "date_hit_3mo": None,
                "hit_in_6mo": "no data", "date_hit_6mo": None,
            })
            continue

        hit3, date3, days3 = check_hit(price_df, entry_date, window_3mo_end, strike, cp)
        hit6, date6, days6 = check_hit(price_df, entry_date, window_6mo_end, strike, cp)

        results.append({
            "ticker": ticker, "cp": cp, "strike": strike,
            "entry_date": entry_date.date(),
            "hit_in_3mo": "Yes" if hit3 else "No", "date_hit_3mo": date3,
            "hit_in_6mo": "Yes" if hit6 else "No", "date_hit_6mo": date6,
            "days_to_hit_3mo": days3,
            "days_to_hit_6mo": days6,
        })

    out = pd.DataFrame(results)
    out_path = "strike_hit_results.csv"
    out.to_csv(out_path, index=False)
    hit3_days = out["days_to_hit_3mo"].dropna()
    hit6_days = out["days_to_hit_6mo"].dropna()
    print(f"Avg days to hit (3mo window): {hit3_days.mean():.1f}  (median {hit3_days.median():.0f}, n={len(hit3_days)})")
    print(f"Avg days to hit (6mo window): {hit6_days.mean():.1f}  (median {hit6_days.median():.0f}, n={len(hit6_days)})")
    print(f"\nWrote {len(out)} rows to {out_path}")

    

if __name__ == "__main__":
    main()
