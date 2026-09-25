#!/usr/bin/env python3
"""
MARKET REGIME FILTER — options strategy gating for SPX
================================================================
Classifies the SPX environment into 4 behavioral regimes so execution
models know whether to run premium-selling vs long-vol/breakout systems.

HONEST FRAMING (read before trading on it):
  Regime models reliably classify VOLATILITY + TREND STATE. They do NOT
  predict direction — a "bullish trend" regime tells you the recent
  character of the tape, not where it goes next. Use this to GATE
  strategy TYPE (sell premium in calm/range regimes, buy premium in
  expanding-vol regimes), not to bet direction. The thresholds below are
  reasonable priors, NOT validated constants — backtest them on your own
  SPX+VIX history and tune. Regime membership is also lagged (it's built
  from trailing windows), so it confirms the environment, it doesn't
  call the turn.

Parts:
  1. Feature engineering (vectorized): ATR ratio, Hurst/ADX trend
     persistence, distance-from-200SMA, VIX z-score.
  2. Classification: rules-based (primary, interpretable) + optional
     KMeans (secondary, for discovering natural clusters).
  3. Strategy mapping: which options structures are permitted/blocked.

Runnable out-of-the-box on mock data. Swap `mock_data()` for real
SPX OHLCV + VIX to use for real.
"""

import numpy as np
import pandas as pd
from scipy import stats
import yfinance as yf


# ══════════════════════════════════════════════════════════════════
# PART 0 — MOCK DATA (replace with real SPX OHLCV + VIX)
# ══════════════════════════════════════════════════════════════════

def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def real_data(years=5):
    spx = yf.download("^GSPC", period=f"{years}y", progress=False)
    vix = yf.download("^VIX", period=f"{years}y", progress=False)["Close"]
    spx = flatten_columns(spx)
    spx = spx.rename(columns=str.lower)
    spx["vix"] = vix
    return spx[["open", "high", "low", "close", "volume", "vix"]].dropna()  # columns: open, high, low, close, volume, vix

    # regime-switching vol: alternate low/high vol blocks
    block = 60
    vol = np.empty(n)
    trend_mu = np.empty(n)
    for i in range(0, n, block):
        hi = (i // block) % 2 == 0          # alternate
        vol[i:i+block] = rng.uniform(0.004, 0.008) if hi else rng.uniform(0.015, 0.030)
        # some blocks trend, some chop
        chop = (i // block) % 3 == 0
        trend_mu[i:i+block] = 0.0 if chop else rng.choice([-1, 1]) * rng.uniform(0.0003, 0.0009)

    rets = rng.normal(trend_mu, vol)
    close = 4000 * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, vol)))
    low = close * (1 - np.abs(rng.normal(0, vol)))
    open_ = np.r_[close[0], close[:-1]]
    volu = rng.integers(1_000_000, 5_000_000, n)

    # VIX: inverse-ish to price moves, scaled off realized vol
    vix = 12 + vol * 900 + rng.normal(0, 1.5, n)
    vix = np.clip(vix, 9, 80)

    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close,
        "volume": volu, "vix": vix,
    }, index=dates)


# ══════════════════════════════════════════════════════════════════
# PART 1 — FEATURE ENGINEERING (vectorized)
# ══════════════════════════════════════════════════════════════════

def atr(df, window):
    """Average True Range."""
    h, l, c = df["high"], df["low"], df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def atr_ratio(df, fast=9, slow=50):
    """Fast/slow ATR. >1 = volatility expanding, <1 = compressing."""
    return atr(df, fast) / atr(df, slow)


def adx(df, window=14):
    """ADX — trend persistence strength (0-100). >25 ~ trending."""
    h, l, c = df["high"], df["low"], df["close"]
    up = h.diff()
    dn = -l.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr_ = pd.Series(tr).rolling(window).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(window).mean() / atr_
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(window).mean() / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(window).mean()


def hurst(series, max_lag=20):
    """Hurst exponent via rescaled-range/variance-of-lagged-diffs.
    >0.5 = trending/persistent, <0.5 = mean-reverting, ~0.5 = random walk.
    Returns a single float for the given window of prices."""
    series = np.asarray(series, dtype=float)
    if len(series) < max_lag + 2 or np.any(~np.isfinite(series)):
        return np.nan
    lags = range(2, max_lag)
    tau = [np.std(series[lag:] - series[:-lag]) for lag in lags]
    tau = np.array(tau)
    if np.any(tau <= 0):
        return np.nan
    # slope of log(tau) vs log(lag) is the Hurst exponent
    m = np.polyfit(np.log(list(lags)), np.log(tau), 1)
    return m[0]


def rolling_hurst(close, window=100, max_lag=20):
    """Rolling Hurst — trend-persistence over time. Expensive; window keeps it sane."""
    return close.rolling(window).apply(lambda x: hurst(x, max_lag), raw=True)


def dist_from_sma(df, window=200):
    """Standardized distance of price from its long SMA (trend location)."""
    sma = df["close"].rolling(window).mean()
    resid = df["close"] - sma
    z = (resid - resid.rolling(window).mean()) / resid.rolling(window).std()
    return z


def vix_zscore(df, window=100):
    """Rolling z-score of VIX — is vol expanding/compressing vs its baseline."""
    v = df["vix"]
    return (v - v.rolling(window).mean()) / v.rolling(window).std()


def build_features(df):
    """Assemble the feature matrix used for classification."""
    out = pd.DataFrame(index=df.index)
    out["atr_ratio"] = atr_ratio(df)
    out["adx"] = adx(df)
    out["hurst"] = rolling_hurst(df["close"])
    out["dist200"] = dist_from_sma(df)
    out["vix_z"] = vix_zscore(df)
    out["vix"] = df["vix"]
    return out


# ══════════════════════════════════════════════════════════════════
# PART 2 — REGIME CLASSIFICATION
# ══════════════════════════════════════════════════════════════════
#
# Two vol axes and one trend axis drive the 4 regimes:
#   VOL STATE  = high vs low   (VIX z-score + ATR ratio)
#   TREND STATE= trending vs mean-reverting (Hurst/ADX + |dist200|)
#
#   R1 Low-vol  + Trend        -> premium selling (bullish drift)
#   R2 Low-vol  + Mean-revert  -> iron condor / range
#   R3 High-vol + Trend        -> long premium / breakout
#   R4 High-vol + Mean-revert  -> wide-range chaos / mean-revert
#
# WHY RULES over KMeans as the PRIMARY:
#   KMeans finds *natural* clusters but they're unlabeled and unstable —
#   you'd have to re-map cluster IDs to regimes each run, and a cluster
#   boundary can drift with new data, silently changing what "R2" means.
#   For strategy GATING you want INTERPRETABLE, STABLE thresholds a human
#   can audit ("vol high AND trending -> long premium"). Rules give that.
#   KMeans is included below as a discovery tool — run it to SEE how many
#   natural states your data has and whether the 4-regime prior holds, but
#   gate trades on the rules.

# thresholds — PRIORS, tune to your data
VIX_Z_HIGH = 0.5          # vix z above this = high-vol state
ATR_EXPAND = 1.10         # fast/slow ATR above this = expanding
TREND_HURST = 0.55        # hurst above this = persistent/trending
TREND_ADX = 22            # adx above this = trending
DIST_TREND = 1.0          # |z dist from 200sma| above this = extended/trending


def classify_rules(feat):
    """Rules-based regime per row. Returns a Series of 1-4 (or NaN if features missing)."""
    f = feat
    high_vol = (f["vix_z"] > VIX_Z_HIGH) | (f["atr_ratio"] > ATR_EXPAND)
    trending = (f["hurst"] > TREND_HURST) | (f["adx"] > TREND_ADX) | (f["dist200"].abs() > DIST_TREND)

    regime = pd.Series(np.nan, index=f.index)
    regime[(~high_vol) & (trending)] = 1     # low vol, trend
    regime[(~high_vol) & (~trending)] = 2    # low vol, mean-revert
    regime[(high_vol) & (trending)] = 3      # high vol, trend
    regime[(high_vol) & (~trending)] = 4     # high vol, mean-revert
    return regime


def classify_kmeans(feat, k=4, seed=7):
    """OPTIONAL discovery tool. Clusters the standardized features into k groups.
    Returns cluster labels (0..k-1) — NOT mapped to regime meaning. Use to
    EXPLORE natural structure, not to gate trades (see note above)."""
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        print("sklearn not installed — skipping KMeans (pip install scikit-learn)")
        return None
    cols = ["atr_ratio", "adx", "hurst", "dist200", "vix_z"]
    X = feat[cols].dropna()
    Xs = (X - X.mean()) / X.std()
    labels = KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(Xs)
    return pd.Series(labels, index=X.index)


# ══════════════════════════════════════════════════════════════════
# PART 3 — STRATEGY MAPPING
# ══════════════════════════════════════════════════════════════════

REGIME_INFO = {
    1: {
        "name": "Low-Vol Bullish Trend",
        "desc": "Calm, drifting up. Premium-selling environment.",
        "permit": ["Short Put Spread", "Covered Call", "Put Credit Spread", "Cash-Secured Put"],
        "block":  ["Long Straddle", "Long Strangle", "Debit Spreads (net long vega)"],
    },
    2: {
        "name": "Low-Vol Range / Choppy",
        "desc": "Calm, mean-reverting. Range-bound premium harvest.",
        "permit": ["Short Iron Condor", "Short Strangle (defined)", "Butterfly", "Calendar"],
        "block":  ["Directional Debit Spreads", "Long Straddle"],
    },
    3: {
        "name": "High/Expanding-Vol Trend",
        "desc": "Vol expanding, directional. Long-premium / breakout.",
        "permit": ["Long Call/Put Debit Spread", "Long Straddle (into expansion)", "Backspread"],
        "block":  ["Short Iron Condor", "Naked Short Premium", "Short Strangle"],
    },
    4: {
        "name": "High-Vol Chaotic / Mean-Revert",
        "desc": "Vol high, whipsawing. Wide-range mean reversion or stand aside.",
        "permit": ["Wide Iron Condor (far OTM)", "Ratio spreads", "REDUCE SIZE / cash"],
        "block":  ["Tight Credit Spreads", "0DTE naked", "Anything gamma-short near ATM"],
    },
}


def strategy_for(regime):
    """Print permitted/blocked strategies for a regime int."""
    if regime not in REGIME_INFO:
        print(f"Regime {regime}: unknown / insufficient data — STAND ASIDE")
        return
    r = REGIME_INFO[regime]
    print(f"\nREGIME {regime}: {r['name']}")
    print(f"  {r['desc']}")
    print(f"  ✅ PERMIT: {', '.join(r['permit'])}")
    print(f"  ⛔ BLOCK:  {', '.join(r['block'])}")


# ══════════════════════════════════════════════════════════════════
# DEMO
# ══════════════════════════════════════════════════════════════════

def main():
    df = real_data()
    feat = build_features(df)
    feat["regime"] = classify_rules(feat)

    print("=" * 60)
    print("MARKET REGIME FILTER ")
    print("=" * 60)

    # regime distribution
    print("\nRegime distribution (rules):")
    print(feat["regime"].value_counts().sort_index().to_string())

    # current state
    latest = feat.dropna(subset=["regime"]).iloc[-1]
    cur = int(latest["regime"])
    print(f"\nLatest bar: {feat.index[-1].date()}")
    print(f"  atr_ratio {latest['atr_ratio']:.2f} | adx {latest['adx']:.0f} | "
          f"hurst {latest['hurst']:.2f} | dist200 {latest['dist200']:+.2f} | "
          f"vix {latest['vix']:.1f} (z {latest['vix_z']:+.2f})")
    strategy_for(cur)

    # optional: show natural clusters for comparison
    km = classify_kmeans(feat)
    if km is not None:
        print("\nKMeans cluster sizes (discovery only, unlabeled):")
        print(km.value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()