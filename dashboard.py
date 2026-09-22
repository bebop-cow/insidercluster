import os
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import talib
import requests

from scipy.signal import find_peaks
from garch import get_returns, fit_garch, forecast_vol, tail_risk
from iv import current_atm_iv
from twos10s30s import fetch_jgb_daily
from insidercluster_v6 import fetch_recent_form4, analyze
from dotenv import load_dotenv


load_dotenv()
EIA_KEY = os.getenv("EIA_KEY")

def week_delta(series):
    if len(series) < 6:
        return 0.0
    return series.iloc[-1] - series.iloc[-6]      # now vs ~1 week ago


def fetch_close(ticker, period="10y"):
    return yf.Ticker(ticker).history(period=period)["Close"].tz_localize(None).dropna()


@st.cache_data(ttl=3600)
def get_rate_regime(series_id="DGS10", window=100):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url, parse_dates=["observation_date"], index_col="observation_date")
    y10 = pd.to_numeric(df[series_id], errors="coerce").dropna()
    ma = y10.rolling(window).mean()
    rising = y10.iloc[-1] > ma.iloc[-1]
    return y10.iloc[-1], rising, ma.iloc[-1], y10.iloc[-1] - y10.iloc[-21]


@st.cache_data(ttl=3600)
def get_oil():
    s = yf.Ticker("USO").history(period="1mo")["Close"].dropna()
    return s.iloc[-1], week_delta(s)


@st.cache_data(ttl=3600)
def get_jgb():
    s = fetch_jgb_daily().dropna()
    return s.iloc[-1], week_delta(s)


@st.cache_data(ttl=3600)
def get_congress(ticker, limit=10):
    url = "https://www.bargo.ai/free-apis/congress/v1/trades"
    headers = {"User-Agent": "Lazuli Research tyrin@example.com"}
    try:
        r = requests.get(url, params={"ticker": ticker}, headers=headers, timeout=20)
        trades = r.json().get("trades", [])[:limit]
        out = []
        for t in trades:
            out.append((t.get("member"), t.get("type"), t.get("amount_range"),
                        t.get("transaction_date", "?"), t.get("disclosure_date", "?")))
        return out
    except Exception:
        return []

@st.cache_data(ttl=3600)      # slow — cache an hour
def get_insiders():
    filings = fetch_recent_form4()
    return analyze(filings)

@st.cache_data(ttl=3600)
def get_congress_latest(limit=15):
    url = "https://www.bargo.ai/free-apis/congress/v1/trades"
    headers = {"User-Agent": "Lazuli Research tyrin@example.com"}
    try:
        r = requests.get(url, params={"limit": limit}, headers=headers, timeout=20)
        trades = r.json().get("trades", [])[:limit]
        out = []
        for t in trades:
            out.append((t.get("member"), t.get("ticker"), t.get("type"),
                        t.get("amount_range"), t.get("transaction_date","?")))
        return out
    except Exception:
        return []

@st.cache_data(ttl=3600)
def get_vol_regime(ticker):
    ret = get_returns(ticker, years=5)
    fitted = fit_garch(ret)
    daily = forecast_vol(fitted, days=5)
    iv = current_atm_iv(ticker)
    garch_annual = daily.mean() * np.sqrt(252)
    iv_annual = iv * 100 if iv is not None else None
    spread = (iv_annual - garch_annual) if iv_annual else None
    return garch_annual, iv_annual, spread


@st.cache_data(ttl=3600)
def get_tail(ticker):
    ret = get_returns(ticker, years=5)
    fitted = fit_garch(ret)
    spot = fetch_close(ticker).iloc[-1]
    t_move, n_move = tail_risk(fitted, spot, 5, 0.99)
    nu = fitted.params["nu"]
    return spot, t_move, n_move, nu

def rsi(closes, window=14):
    delta = closes.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(uppers=0)
    avg_gain = gains.rolling(window).mean()
    avg_losses = losses.rolling(window).mean()
    rs = avg_gain / avg_losses
    return(100 -100/(1+rs)).iloc[-1]


@st.cache_data(ttl=3600)
def detect_structure(ticker, months=6):
    closes = yf.Ticker(ticker).history(period=f"{months}mo")["Close"].dropna()
    if closes.empty:
        return None
    hi, lo, last = closes.max(), closes.min(), closes.iloc[-1]
    return {
        "last": last, "hi": hi, "lo": lo,
        "pos": (last - lo) / (hi - lo),
        "ma50": closes.rolling(50).mean().iloc[-1],
        "above_ma": last > closes.rolling(50).mean().iloc[-1],
        "near_high": last >= hi * 0.99,
        "near_low": last <= lo * 1.01,
        "closes": closes,
    }
@st.cache_data(ttl=3600)
def get_refinery():
    url = "https://api.eia.gov/v2/petroleum/pnp/wiup/data/"
    params = {
        "api_key": EIA_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": "WPULEUS3",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 8,
    }
    r = requests.get(url, params=params, timeout=20)
    rows = r.json()["response"]["data"]
    latest = float(rows[0]["value"])
    week_ago = float(rows[1]["value"])      # rows are newest-first
    return latest, latest - week_ago, rows[0]["period"]


def detect_double(closes, tolerance=0.03):
    prices = closes.values
    peaks, _ = find_peaks(prices, distance=10)
    troughs, _ = find_peaks(-prices, distance=10)
    double_top = double_bottom = False
    if len(peaks) >= 2:
        top2 = sorted(prices[peaks])[-2:]
        double_top = abs(top2[0] - top2[1]) / top2[1] < tolerance
    if len(troughs) >= 2:
        low2 = sorted(prices[troughs])[:2]
        double_bottom = abs(low2[0] - low2[1]) / low2[1] < tolerance
    return double_top, double_bottom


@st.cache_data(ttl=3600)
def detect_candles(ticker, months=3):
    df = yf.Ticker(ticker).history(period=f"{months}mo").dropna()
    o = df["Open"].values.astype(float)
    h = df["High"].values.astype(float)
    l = df["Low"].values.astype(float)
    c = df["Close"].values.astype(float)
    patterns = {
        "Doji": talib.CDLDOJI(o, h, l, c),
        "Hammer": talib.CDLHAMMER(o, h, l, c),
        "Shooting Star": talib.CDLSHOOTINGSTAR(o, h, l, c),
        "Engulfing": talib.CDLENGULFING(o, h, l, c),
        "Morning Star": talib.CDLMORNINGSTAR(o, h, l, c),
        "Evening Star": talib.CDLEVENINGSTAR(o, h, l, c),
    }
    found = []
    for name, series in patterns.items():
        if series[-1] != 0:
            found.append((name, "bullish" if series[-1] > 0 else "bearish"))
    return found



st.title("Lazuli Capital — Regime Dashboard")

# ticker input FIRST so every section below can use it
ticker = st.text_input("Ticker", "SPY").upper()

# ── Macro row ──
st.header("Macro")
m1, m2, m3 = st.columns(3)
level, rising, ma, rate_chg = get_rate_regime()
m1.metric("US 10Y", f"{level:.2f}%", f"{rate_chg:+.2f}% (1mo)")
oil_px, oil_chg = get_oil()
m2.metric("Oil (USO)", f"${oil_px:.2f}", f"{oil_chg:+.2f} (1wk)")
jgb_px, jgb_chg = get_jgb()
m3.metric("Japan 10Y", f"{jgb_px:.2f}%", f"{jgb_chg:+.2f} (1wk)")
st.caption(f"10Y vs 100d MA {ma:.2f}% → {'RISING (headwind)' if rising else 'FALLING (tailwind)'}")
util, util_chg, util_date = get_refinery()
st.caption(f"US Refinery Utilization: {util:.1f}% ({util_chg:+.1f} wk) — as of {util_date}")


# ── Congress trades ──
st.header("Congress Trades")
trades = get_congress(ticker)
if trades:
    buys = sum(1 for t in trades if t[1] == "purchase")
    sells = len(trades) - buys
    st.caption(f"{buys} buys / {sells} sells on file (disclosure lags up to 45d)")
    for member, ttype, amount, tdate, ddate in trades:
        emoji = "🟢" if ttype == "purchase" else "🔴"
        st.write(f"{emoji} {member} — {ttype} {amount}  ·  traded {tdate}, disclosed {ddate}")
else:
    st.write("• No congressional trades on file for this ticker")

# -- Insider Activity --

st.header("Insider Activity")
buy_rows, sell_rows = get_insiders()

st.subheader("Buy signals")
if buy_rows:
    buy_df = pd.DataFrame([
        {"Ticker": r["ticker"], "Company": r["company"][:30],
         "Insiders": r["insiders"], "Total $": f"${r['total']:,.0f}", 
         "Tag": r["tag"], "Traded": r["last_date"]}
        for r in buy_rows
    ])
    st.dataframe(buy_df, hide_index=True)
else:
    st.write("No buy signals in window")

st.subheader("Sells (watchlist)")
if sell_rows:
    sell_df = pd.DataFrame([
        {"Ticker": r["ticker"], "Company": r["company"][:28],
         "Sellers": r["sellers"], "Total Sold ($M)": round(r['total_sell']/1e6, 1),
         "Traded": r["last_date"]}
        for r in sell_rows
    ])
    st.dataframe(sell_df, hide_index=True)
else:
    st.write("No sell clusters in window")

# ── Vol regime ──
st.header("Vol Regime")
garch_annual, iv_annual, spread = get_vol_regime(ticker)
c1, c2, c3 = st.columns(3)
c1.metric("GARCH vol", f"{garch_annual:.1f}%")
c2.metric("IV", f"{iv_annual:.1f}%" if iv_annual else "n/a")
c3.metric("Spread", f"{spread:+.1f}%" if spread else "n/a",
          "premium RICH — sell" if spread and spread > 5 else "fair/cheap")

# ── Tail risk ──
st.header("Tail Risk (sizing)")
spot, t_move, n_move, nu = get_tail(ticker)
c1, c2, c3 = st.columns(3)
c1.metric("Spot", f"${spot:.2f}")
c2.metric("99% worst 5d (fat-tail)", f"-${t_move:.2f}")
c3.metric("nu (tail fatness)", f"{nu:.1f}", "fat tails" if nu < 6 else "moderate")



# ── Structure ──
st.header("Structure")
s = detect_structure(ticker)
c1, c2, c3 = st.columns(3)
c1.metric("Support", f"${s['lo']:.2f}")
c2.metric("Resistance", f"${s['hi']:.2f}")
c3.metric("Position in range", f"{s['pos']*100:.0f}%")
st.write("• Trend: " + ("above 50d MA" if s["above_ma"] else "below 50d MA"))
if s["near_high"]: st.write("• At/near 6mo HIGH")
if s["near_low"]:  st.write("• At/near 6mo LOW")
st.line_chart(s["closes"])
dt, db = detect_double(s["closes"])
if dt: st.write("• Possible DOUBLE TOP")
if db: st.write("• Possible DOUBLE BOTTOM")
if not (dt or db): st.write("• No double top/bottom detected")
candles = detect_candles(ticker)
if candles:
    for name, direction in candles:
        st.write(f"• Candlestick: {name} ({direction}) — suggestive only")
else:
    st.write("• No candlestick pattern on latest bar")

# -- RSI --
r = rsi(s["closes"])
label = "OVERBOUGHT" if r >= 70 else ("OVERSOLD" if r <= 30 else "neutral")
st.write(f"• RSI(14): {r:.1f} - {label}")

# ── Stance (synthesized) ──
st.header("Stance")
notes = []
size_mult = 1.0
if rising:
    notes.append("Rates RISING — headwind. Reduce directional risk.")
    size_mult *= 0.7
else:
    notes.append("Rates FALLING — tailwind. Normal risk budget.")
if spread and spread > 5:
    notes.append(f"Premium RICH ({spread:+.1f}%) — favor selling vol.")
elif spread and spread < 0:
    notes.append(f"Premium CHEAP ({spread:+.1f}%) — favor buying vol/protection.")
else:
    notes.append("Premium fair — no strong vol edge.")
if nu < 5:
    notes.append(f"FAT tails (nu {nu:.1f}) — size down, respect gap risk.")
    size_mult *= 0.7
for n in notes:
    st.write("• " + n)
st.metric("Suggested size multiplier", f"{size_mult:.2f}x")
st.caption("Markers describe the environment. They do not predict direction.")