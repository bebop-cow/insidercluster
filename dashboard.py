import streamlit as st
import pandas as pd

st.title("Lazuli Capital - Regime Dashboard")

@st.cache_data(ttl=3600) 
def get_rate_regime(series_id="DGS10", window=100):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	y10 = pd.to_numeric(df[series_id], errors = "coerce")
	ma = ma.rolling(window).mean()
	rising = y10.iloc[-1] > ma.iloc[-1]
	return y10.iloc[-1], rising


level, rising = get_rate_regime()
st.metric("10Y Yield", f"{level:.2f}%", "RISING (headwind)" if rising else "FALLING (tailwind)")