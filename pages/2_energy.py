import streamlit as st
import yfinance as yf
import pandas as pd

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from energyscorecard import rel_strength, scorecard, get_eia_series

st.title("⚡ Energy Sector — Lazuli")

st.header("Sector Scorecard")
sectors = {"Oil": "XLE", "Solar": "TAN", "Nuclear": "URA"}
for name, tk in sectors.items():
	rs = rel_strength(tk)
	closes = yf.Ticker(tk).history(period="6mo")["Close"].dropna()
	ma50 = closes.rolling(50).mean().iloc[-1]
	trend = "🟢 uptrend" if closes.iloc[-1] > ma50 else "🔴 downtrend"
	st.metric(f"{name} ({tk})", f"RS {rs:+.1f}% vs SPY")
	st.caption(trend)

@st.cache_data(ttl=3600)
def oil_fundamentals():
	stocks =  get_eia_series("WCESTUS1", "stoc/wstk")
	prod = get_eia_series("WCRFPUS2", "sum/sndw")
	spr =  get_eia_series("WCSSTUS1", "sum/sndw")
	gasd = get_eia_series("WGFUPUS2", "sum/sndw")
	return {
		"stock_chg": stocks[0][1] - stocks[4][1],
        "prod_chg":  prod[0][1] - prod[4][1],
        "spr_chg":   spr[0][1] - spr[4][1],
        "gas_chg":   gasd[0][1] - gasd[4][1],
	}

st.header("Oil Fundamentals (EIA, 4-week)")
f = oil_fundamentals()
c1, c2 = st.columns(2)
c1.metric("Crude Inventories", f"{f['stock_chg']:+,.0f}k",
          "DRAW (bullish)" if f['stock_chg'] < 0 else "BUILD (bearish)")
c2.metric("US Production", f"{f['prod_chg']:+,.0f}k/d",
          "RISING (bearish)" if f['prod_chg'] > 0 else "FALLING (bullish)")
c3, c4 = st.columns(2)
c3.metric("SPR", f"{f['spr_chg']:+,.0f}k",
          "RELEASING (bearish)" if f['spr_chg'] < 0 else "REFILLING (bullish)")
c4.metric("Gasoline Demand", f"{f['gas_chg']:+,.0f}k/d",
          "RISING (bullish)" if f['gas_chg'] > 0 else "FALLING (bearish)")


st.header("Nuclear Basket")
nuclear = {
    "Miner": ["CCJ"], "Enrich": ["LEU"],
    "SMR": ["OKLO", "NNE", "SMR"],
    "AI-Utility": ["CEG", "VST", "TLN"],
    "Uranium": ["URA", "SRUUF"],
}
rows = []
for group, tickers in nuclear.items():
    for tk in tickers:
        try:
            rs = rel_strength(tk)
            closes = yf.Ticker(tk).history(period="6mo")["Close"].dropna()
            up = closes.iloc[-1] > closes.rolling(50).mean().iloc[-1]
            rows.append({"Group": group, "Ticker": tk,
                         "RS vs SPY": round(rs, 1),
                         "Trend": "🟢 up" if up else "🔴 down"})
        except Exception:
            rows.append({"Group": group, "Ticker": tk,
                         "RS vs SPY": None, "Trend": "no data"})
st.dataframe(pd.DataFrame(rows), hide_index=True)