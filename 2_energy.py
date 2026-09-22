import streamlit as st
import yfinance as yf
import pandas as pd

from Claude.energyscorecard import rel_strength, scorecard

st.title("⚡ Energy Sector — Lazuli")

st.header("Sector Scorecard")
sectors = {"Oil": "XLE", "Solar": "TAN", "Nuclear": "URA"}
for name, tk in sectors.items():
	rs = rel_strength(tk)
	closes = yf.Ticker(tk).history(period="6mo"["Close"]).dropna()
	ma50 = closes.rolling(50).mean().iloc[-1]
	trend = "🟢 uptrend" if closes.iloc[-1] > ma50 else "🔴 downtrend"
	st.metric(f"{name} ({tk})", f"RS {rs:+.1f}% vs SPY", trend)
