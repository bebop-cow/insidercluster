#!/usr/bin/env python3
"""
VOLATILITY ANALYZER · v1  (RV vs IV divergence + earnings IV ramp)
================================================================
TWO THINGS THIS MEASURES:

1. IV vs RV DIVERGENCE  (Tool 3)
   · IV = implied volatility, from TODAY's live option chain (yfinance
     gives us this — the market's forecast of future movement).
   · RV = realized volatility, computed from PAST price history (how
     much the stock ACTUALLY moved).
   · The gap is the signal:
       IV > RV  → options EXPENSIVE (movement priced in > delivered) → lean SELL premium
       IV < RV  → options CHEAP (stock moves more than priced)       → lean BUY premium
   · The ratio IV/RV is the "volatility risk premium." >1 most of the
     time (fear premium) — the question is HOW MUCH over 1.

2. EARNINGS IV RAMP  (Tool 4, Question-1 version)
   · Does volatility rise into an earnings date and collapse after?
   · We can't get historical IV free, so we PROXY the ramp using
     realized vol in the windows around past earnings dates.
   · LIMITATION (read this): this measures the VOLATILITY pattern,
     not your actual option P&L. Real ramp-trade profit needs
     historical OPTION PRICES (theta + delta + vega), which we don't
     have free. This tells you IF vol ramps, not IF the trade paid.

DATA: yfinance only. Live IV from option_chain(), price history for RV.

Run:
  python3 vol_analyzer.py NVDA GOOGL ORCL AVGO
  python3 vol_analyzer.py            # uses default watchlist
================================================================
"""

import sys
import math
import numpy as np
import pandas as pd
from iv import implied_vol, bs_call_price

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

DEFAULT_TICKERS = ["NVDA", "GOOGL", "ORCL", "AVGO", "TSM", "ARM", "V"]

RV_WINDOW = 30          # trading days for realized-vol calc
TRADING_DAYS = 252      # annualization factor
RAMP_PRE_DAYS = 14      # your typical entry: 14 days before earnings
RAMP_POST_DAYS = 5      # window after earnings to measure the crush


# ── helper: flatten yfinance's MultiIndex columns (you know this one) ──
def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# ── RV: realized (historical) volatility ──────────────────────────────
def realized_vol(price_df, window=RV_WINDOW):
    """
    Annualized realized volatility from daily closes.
    Formula: std(daily log returns) × sqrt(252).
    Returns the most recent `window`-day RV as a percent (e.g. 42.3).
    """
    closes = price_df["Close"].dropna()
    if len(closes) < window + 1:
        return None
    log_returns = np.log(closes / closes.shift(1)).dropna()
    recent = log_returns.tail(window)
    daily_std = recent.std()
    annualized = daily_std * math.sqrt(TRADING_DAYS)
    return float(annualized * 100)


def realized_vol_in_window(price_df, end_date, window=RV_WINDOW):
    """
    RV over the `window` trading days ENDING at end_date.
    Used for the earnings-ramp measurement (vol just before a date).
    """
    closes = price_df["Close"].dropna()
    sub = closes[closes.index <= end_date]
    if len(sub) < window + 1:
        return None
    log_returns = np.log(sub / sub.shift(1)).dropna()
    recent = log_returns.tail(window)
    return float(recent.std() * math.sqrt(TRADING_DAYS) * 100)

def pick_expiry(tk, min_days=3):
    for exp in tk.options:
        days_to_expiry = (pd.Timestamp(exp) - pd.Timestamp.now()).days
        if days_to_expiry >= min_days:
            return exp
    return tk.options[-1]


# ── IV: implied volatility from the live option chain ─────────────────
def current_atm_iv(ticker):
    tk = yf.Ticker(ticker)
    expiry = pick_expiry(tk, 5)
    calls = tk.option_chain(expiry).calls
    spot = tk.history(period="1d")["Close"].iloc[-1]
    days = (pd.Timestamp(expiry) - pd.Timestamp.now()).days
    #nearest to money strike with a real price
    calls =calls[calls["lastPrice"] > 0.05]
    nearest = (calls["strike"] - spot).abs().idxmin()
    row = calls.loc[nearest]
    return implied_vol(row["lastPrice"], spot, row["strike"], days)


# ── earnings ramp: RV before vs after each past earnings date ─────────
def earnings_ramp(ticker_obj, price_df):
    """
    For each recent earnings date, compare realized vol in the window
    BEFORE the date vs the window AFTER. If vol ramps into earnings and
    crushes after, RV_before < RV_after_that_spans_the_event... actually
    the cleaner read: measure RV ending the day before earnings (the
    'ramp') vs RV in the days right after (the 'crush aftermath').

    Returns a list of dicts per earnings date. This is a PROXY — see
    the file header's limitation note.
    """
    results = []
    try:
        edates = ticker_obj.get_earnings_dates(limit=12)
        if edates is None or len(edates) == 0:
            return results
        for edate in edates.index:
            edate = pd.Timestamp(edate).tz_localize(None)
            pre = realized_vol_in_window(price_df, edate, RAMP_PRE_DAYS)
            # RV measured a bit AFTER earnings, to capture post-event move
            closes = price_df["Close"].dropna()
            after_slice = closes[closes.index > edate].head(RAMP_POST_DAYS)
            post = None
            if len(after_slice) >= 2:
                lr = np.log(after_slice / after_slice.shift(1)).dropna()
                if len(lr) >= 1:
                    post = float(lr.std() * math.sqrt(TRADING_DAYS) * 100)
            if pre is not None and post is not None:
                results.append({"date": edate.strftime("%Y-%m-%d"),
                                "rv_pre": pre, "rv_post": post})
    except Exception:
        pass
    return results


        
        


# ══════════════════════════════════════════════════════════════════════
# MAIN — WE BUILD THIS TOGETHER. Skeleton below; you fill the logic.
# ══════════════════════════════════════════════════════════════════════
def main():
     tickers = [a.upper() for a in sys.argv[1:]] or DEFAULT_TICKERS
     current_atm_iv(tickers)

    # print("=" * 64)
    # print("VOLATILITY ANALYZER · IV vs RV divergence + earnings ramp")
    # print("=" * 64)

    # # ---- STEP 1: loop over tickers -----------------------------------
    # # For each ticker you need to:
    # #   a) create the yfinance Ticker object
    # #   b) download ~1 year of price history (for RV)
    # #   c) flatten the columns (MultiIndex gotcha)
    # #   d) get the current spot price (last close)
    # #   e) compute RV  → realized_vol(price_df)
    # #   f) compute IV  → current_atm_iv(ticker_obj, spot)
    # #   g) compute the divergence (IV/RV ratio, and IV - RV)
    # #   h) store all that in a row dict, append to a list
    # #
    # # TODO (you): write the loop.
    # rows = []
    # for tk in tickers:
    #     ticker_obj = yf.Ticker(tk)
    #     price_df = yf.download(tk, period="1y", progress=False)
    #     if price_df.empty:
    #         continue
    #     price_df = flatten_columns(price_df)
    #     last_close = price_df["Close"].iloc[-1]
    #     rv = realized_vol(price_df)
    #     iv = current_atm_iv(ticker_obj,last_close)
    #     if rv is None or iv is None:
    #         continue
    #     divergence_ratio = iv/rv
    #     divergence_diff = iv - rv

    #     rows.append({"ticker":tk, "spot": last_close, 
    #             "iv": iv, "rv": rv, "ratio": divergence_ratio, "diff": divergence_diff})


    # # ---- STEP 2: print the IV vs RV table ----------------------------
    # # Columns: TICKER, SPOT, IV%, RV%, IV/RV ratio, and a verdict
    # # (ratio > ~1.2 = options rich → SELL lean; < ~1.0 = cheap → BUY lean)
    # #
    # # TODO (you): print a header, then a row per ticker.
    # print(f"\n{'TICKER':<7}{'SPOT':<9}{'IV%':<8}{'RV%':<8}{'IV/RV':<8}VERDICT")
    # print("-" * 50)
    # for r in rows:
    #     # TODO: compute a verdict string from r["ratio"]
    #     #   ratio > 1.2  → options RICH  → "SELL premium"
    #     #   ratio < 1.0  → options CHEAP → "BUY premium"
    #     #   in between    → "neutral"
    #     if r["ratio"] > 1.2:
    #         verdict = "SELL premium"
    #     elif r["ratio"] < 1.0:
    #         verdict = "BUY premium"
    #     else:
    #         verdict = "neutral"
        
    #     print(f"{r['ticker']:<7}${r['spot']:<8.2f}{r['iv']:<8.1f}"
    #           f"{r['rv']:<8.1f}{r['ratio']:<8.2f}{verdict}")

    # # ---- STEP 3 (optional): earnings ramp per ticker -----------------
    # # For each ticker, call earnings_ramp() and show whether RV was
    # # elevated around past earnings dates.
    # #
    # # TODO (you
    # print(f"\n{'='*50}")
    # print("EARNINGS VOL PATTERN (RV before vs after each print)")
    # print("=" * 50)
    # for r in rows:
    #     tk = r["ticker"]
    #     ticker_obj = yf.Ticker(tk)
    #     price_df = flatten_columns(yf.download(tk, period="1y", progress=False))
    #     ramps = earnings_ramp(ticker_obj, price_df)
    #     if not ramps:
    #         continue
    #     print(tk)
    #     for d in ramps:
    #         print(f"   {d['date']}:  pre {d['rv_pre']:.1f}%  →  post {d['rv_post']:.1f}%")



if __name__ == "__main__":
    main()