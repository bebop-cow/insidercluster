import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import talib

from scipy.signal import find_peaks
from garch import get_returns, fit_garch, forecast_vol, tail_risk, fetch_close
from iv import current_atm_iv


st.title("Lazuli Capital - Regime Dashboard")


@st.cache_data(ttl=3600) 
def get_rate_regime(series_id="DGS10", window=100):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	y10 = pd.to_numeric(df[series_id], errors = "coerce").dropna()
	ma = y10.rolling(window).mean()
	rising = y10.iloc[-1] > ma.iloc[-1]
	return y10.iloc[-1], rising, ma.iloc[-1], y10.iloc[-1] - y10.iloc[-21]

level, rising, ma, chg_1m = get_rate_regime()
st.metric("10Y Yield", f"{level:.2f}%",
          f"{chg_1m:+.2f}% (1mo)")
st.caption(f"100d MA: {ma:.2f}%  →  {'RISING (headwind)' if rising else 'FALLING (tailwind)'}")

st.header("Vol Regime")
ticker = st.text_input("Ticker", "SPY").upper()
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

garch_annual, iv_annual, spread = get_vol_regime(ticker)
c1, c2, c3 = st.columns(3)
c1.metric("GARCH vol", f"{garch_annual:.1f}%")
c2.metric("IV", f"{iv_annual:.1f}%" if iv_annual else "n/a")
c3.metric("Spread", f"{spread:+.1f}%" if spread else "n/a",
	"premium RICH — sell" if spread and spread > 5 else "fair/cheap")

@st.cache_data(ttl=3600)
def get_tail(ticker):
    ret = get_returns(ticker, years=5)
    fitted = fit_garch(ret)
    spot = fetch_close(ticker).iloc[-1]
    t_move, n_move = tail_risk(fitted, spot, 5, 0.99)
    nu = fitted.params["nu"]
    return spot, t_move, n_move, nu

st.header("Tail Risk (sizing)")
spot, t_move, n_move, nu = get_tail(ticker)
c1, c2, c3 = st.columns(3)
c1.metric("Spot", f"${spot:.2f}")
c2.metric("99% worst 5d (fat-tail)", f"-${t_move:.2f}")
c3.metric("nu (tail fatness)", f"{nu:.1f}", "fat tails" if nu < 6 else "moderate")

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

def detect_structure(ticker, months=6):
	tk = yf.Ticker(ticker)
	closes = tk.history(period=f"{months}mo")["Close"].dropna()
	if closes is None:
		return None
	hi = closes.max()
	lo = closes.min()
	last = closes.iloc[-1]
	pos_in_range = (last - lo) / (hi - lo)
	ma50 = closes.rolling(50).mean().iloc[-1]
	above_ma = last >ma50
	# breakout is today with 1% pf the window?
	near_high = last >= hi * 0.99
	near_low = last <= lo * 1.01
	return {"last": last, "hi":hi, "lo": lo, "pos":pos_in_range,
			"ma50": ma50, "above_ma":above_ma, 
			"near_high": near_high, "near_low":near_low, "closes":closes}

def detect_double(closes, tolerance=0.03):
    prices = closes.values
    peaks, _ = find_peaks(prices, distance=10)      # local maxima, 10 days apart min
    troughs, _ = find_peaks(-prices, distance=10)   # local minima

    double_top = False
    if len(peaks) >= 2:
        top2 = sorted(prices[peaks])[-2:]           # two highest peaks
        if abs(top2[0] - top2[1]) / top2[1] < tolerance:
            double_top = True

    double_bottom = False
    if len(troughs)>=2:
    	low2 = sorted(prices[troughs])[:2]
    	if abs(low2[0] - low2[1]) / low2[1] < tolerance:
    		double_bottom = True

    return double_top, double_bottom

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
if dt: st.write("• Possible DOUBLE TOP ")
if db: st.write("• Possible DOUBLE BOTTOM")
if not (dt or db): st.write("• No double top/bottom detected")


def detect_candles(ticker, months=3):
    tk = yf.Ticker(ticker)
    df = tk.history(period=f"{months}mo").dropna()      # note the .dropna() reflex
    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]

    patterns = {
        "Doji": talib.CDLDOJI(o, h, l, c),
        "Hammer": talib.CDLHAMMER(o, h, l, c),
        "Shooting Star": talib.CDLSHOOTINGSTAR(o, h, l, c),
        "Bullish Engulfing": talib.CDLENGULFING(o, h, l, c),
        "Morning Star": talib.CDLMORNINGSTAR(o, h, l, c),
        "Evening Star": talib.CDLEVENINGSTAR(o, h, l, c),
    }
    # check the most recent bar for each
    found = []
    for name, series in patterns.items():
        val = series.iloc[-1]
        if val != 0:
            found.append((name, "bullish" if val > 0 else "bearish"))
    return found

candles = detect_candles(ticker, 3)
if candles:
    for name, direction in candles:
        st.write(f"• Candlestick: {name} ({direction}) — suggestive only")
else:
    st.write("• No candlestick pattern on latest bar")