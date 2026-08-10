#!/usr/bin/env python3
"""
IRAN EVENT STUDY · v1  (how did QQQ / semis behave around the threat<->deal cycle?)
====================================================================================
WHAT THIS IS:
  A BACKWARD-LOOKING event study. For each dated Iran-related event
  (tagged ESCALATION or DEESCALATION *before* looking at any returns),
  measure how the underlying moved in short windows around the event.

WHAT THIS IS NOT:
  A predictive timer. It does NOT say "a threat just happened, position
  now." The whole reason it can't is baked into the data: several 2026
  "threats" were NOT walked back — they became real strikes and a real
  war. A fade-the-escalation trade would have worked on the bluffs and
  been catastrophically wrong on the strikes that actually landed, and
  you cannot tell which is which at the moment the threat fires.

HONEST GUARDRAILS (built into the output):
  · Sample size is TINY (~7 escalations, ~4 de-escalations). This is a
    descriptive CATALOG of what happened each time, not a distribution
    you can trust a mean from. The per-event table is the real content;
    the aggregate is shown but flagged as statistically meaningless.
  · Each event carries a `walked_back` flag. Escalations that became
    real strikes are marked False — those are the left-tail cases a
    timer would blow up on.
  · No transaction costs, no options mechanics. Cash-index moves only.

METHODOLOGY NOTES:
  · Event date = the day the news BROKE (sourced from reporting). If the
    news broke after the close or on a non-trading day, we anchor to the
    NEXT available trading day (the first session that could react).
  · "window +N" = cumulative % return from the event-day close to the
    close N trading days later. "window -1" = the day-before return, for
    context (was the market already moving in?).
  · Dates were tagged ESC/DEESC by headline content only, before returns
    were computed. Don't re-tag based on what the chart did.

UNDERLYINGS: QQQ (Nasdaq-100) and SOXX (semis ETF, as ^SOX proxy).

Run:
  python3 iran_event_study.py
  python3 iran_event_study.py QQQ
  python3 iran_event_study.py SOXX
====================================================================================
"""

import sys
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

DEFAULT_TICKERS = ["QQQ", "SOXX"]
WINDOWS = [1, 3, 5]          # trading-day horizons to measure after the event
PRE_WINDOW = 1               # days before, for run-in context

# ── EVENT TABLE ───────────────────────────────────────────────────────
# Tagged by headline content BEFORE any returns were looked at.
# tag:         "ESC" (escalation/threat/strike) or "DEESC" (walk-back/deal)
# walked_back: for ESC events — did the threat get pulled back (True) or
#              did it become a real strike/war (False)? For DEESC, None.
# Sources: Wikipedia (2026 Iran war; ceasefire), CFR, Britannica,
#          Newsweek, CRS. Dates are when the news broke.
EVENTS = [
    # date          tag      walked_back  label
    ("2025-06-13", "ESC",   False, "Israel opens strikes; Iran exits talks"),
    ("2025-06-21", "ESC",   True,  "Trump Strait-of-Hormuz invasion threat"),
    ("2026-02-28", "ESC",   False, "US/Israel strikes; war begins"),
    ("2026-03-06", "ESC",   True,  "'UNCONDITIONAL SURRENDER' post"),
    ("2026-03-21", "ESC",   True,  "Threat to hit civilian energy infra"),
    ("2026-05-25", "ESC",   False, "Renewed US strikes on southern Iran"),
    ("2026-06-11", "ESC",   True,  "'Very hard tonight' threat (cancelled same day)"),

    ("2026-04-08", "DEESC", None,  "US-Iran-Israel ceasefire agreed"),
    ("2026-04-21", "DEESC", None,  "Trump extends ceasefire indefinitely"),
    ("2026-06-11", "DEESC", None,  "Strikes cancelled; 'deal wrapped up'"),
    ("2026-06-17", "DEESC", None,  "60-day ceasefire MOU signed"),
]


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def load_prices(ticker):
    """Download daily closes covering the full event span with padding."""
    start = "2025-05-01"
    end = pd.Timestamp.now().strftime("%Y-%m-%d")
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return None
    df = flatten_columns(df)
    df = df[["Close"]].copy()
    return df


def anchor_index(price_index, date_str):
    """
    Map an event date to a position in the trading calendar.
    If the date is a trading day, use it. If not (weekend/holiday/after
    close), anchor to the NEXT available trading day — the first session
    that could actually react.
    Returns the integer position in price_index, or None if out of range.
    """
    d = pd.Timestamp(date_str)
    # positions of all trading days on or after the event date
    later = price_index[price_index >= d]
    if len(later) == 0:
        return None
    first_reacting_day = later[0]
    return price_index.get_loc(first_reacting_day)


def window_return(closes, pos, horizon):
    """
    Cumulative % return from the event-day close to `horizon` trading days
    later. Negative horizon looks backward. Returns None if out of range.
    """
    target = pos + horizon
    if target < 0 or target >= len(closes):
        return None
    base = closes.iloc[pos]
    end = closes.iloc[target]
    return (end / base - 1.0) * 100.0


def study_ticker(ticker):
    prices = load_prices(ticker)
    if prices is None:
        print(f"  No data for {ticker}.")
        return

    closes = prices["Close"]
    idx = prices.index

    print("=" * 74)
    print(f"IRAN EVENT STUDY · {ticker} · cash-index moves around dated events")
    print("=" * 74)
    print(f"Loaded {len(closes)} trading days "
          f"({idx[0].date()} → {idx[-1].date()})\n")

    # per-event measurement, grouped by tag
    rows_by_tag = {"ESC": [], "DEESC": []}

    header = (f"  {'date':<12}{'tag':<7}{'wb':<6}"
              f"{'-1d':>8}{'+1d':>8}{'+3d':>8}{'+5d':>8}  label")
    print(header)
    print("  " + "-" * (len(header) - 2))

    for date_str, tag, walked_back, label in EVENTS:
        pos = anchor_index(idx, date_str)
        if pos is None:
            print(f"  {date_str:<12}{tag:<7}{'—':<6}"
                  f"{'(date outside price range)':>32}  {label}")
            continue

        pre = window_return(closes, pos, -PRE_WINDOW)
        rets = {h: window_return(closes, pos, h) for h in WINDOWS}

        wb = "" if walked_back is None else ("yes" if walked_back else "NO")

        def fmt(x):
            return f"{x:+.2f}" if x is not None else "  n/a"

        print(f"  {date_str:<12}{tag:<7}{wb:<6}"
              f"{fmt(pre):>8}{fmt(rets[1]):>8}{fmt(rets[3]):>8}{fmt(rets[5]):>8}"
              f"  {label}")

        rows_by_tag[tag].append(rets)

    # aggregates — shown, but flagged as statistically meaningless
    print("\n  " + "-" * (len(header) - 2))
    print("  AGGREGATE (mean of per-event window returns):")
    for tag in ("ESC", "DEESC"):
        rows = rows_by_tag[tag]
        n = len(rows)
        if n == 0:
            print(f"    {tag:<7} n=0")
            continue
        means = {}
        for h in WINDOWS:
            vals = [r[h] for r in rows if r[h] is not None]
            means[h] = np.mean(vals) if vals else None
        parts = "  ".join(
            f"+{h}d {means[h]:+.2f}%" if means[h] is not None else f"+{h}d n/a"
            for h in WINDOWS
        )
        print(f"    {tag:<7} n={n:<3} {parts}")

    # split escalations by whether they were walked back
    esc_rows = [(wb, {h: window_return(closes, anchor_index(idx, d), h)
                      for h in WINDOWS})
                for d, t, wb, _ in EVENTS
                if t == "ESC" and anchor_index(idx, d) is not None]
    for flag, name in [(True, "ESC · walked back (bluff)"),
                       (False, "ESC · NOT walked back (real strike)")]:
        subset = [r for wb, r in esc_rows if wb is flag]
        n = len(subset)
        if n == 0:
            continue
        means = {}
        for h in WINDOWS:
            vals = [r[h] for r in subset if r[h] is not None]
            means[h] = np.mean(vals) if vals else None
        parts = "  ".join(
            f"+{h}d {means[h]:+.2f}%" if means[h] is not None else f"+{h}d n/a"
            for h in WINDOWS
        )
        print(f"    {name:<36} n={n:<3} {parts}")

    print()
    print("  READ THIS: n is single digits per bucket. These are anecdotes,")
    print("  not distributions. The 'NOT walked back' row is the left tail a")
    print("  fade-the-threat timer would blow up on — compare it to the")
    print("  'walked back' row and note they are NOT the same trade.\n")


def main():
    tickers = [sys.argv[1].upper()] if len(sys.argv) > 1 else DEFAULT_TICKERS
    for t in tickers:
        study_ticker(t)


if __name__ == "__main__":
    main()