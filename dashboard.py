import streamlit as st
import pandas as pd
import numpy as np

from garch import get_returns, fit_garch, forecast_vol
from iv import current_atm_iv


st.title("Lazuli Capital - Regime Dashboard")


@st.cache_data(ttl=3600) 
def get_rate_regime(series_id="DGS10", window=100):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	y10 = pd.to_numeric(df[series_id], errors = "coerce")
	ma = y10.rolling(window).mean()
	rising = y10.iloc[-1] > ma.iloc[-1]
	return y10.iloc[-1], rising


level, rising = get_rate_regime()
st.metric("10Y Yield", f"{level:.2f}%", "RISING (headwind)" if rising else "FALLING (tailwind)")

st.header("Vol Regime")
ticker = st.text_input("Ticker", "SPY").upper()

def get_vol_regime(ticker):
	ret = get_returns(ticker, years=5)
	fitted = fit_garch(ret)
	daily = forecast_vol(fitted, days=5)
	iv = current_atm_iv(ticker)  
	if iv is None:
		print("\nIV: unavailable (market closed / no quotes)")
	else:
		iv_annual = iv * 100
		garch_annual = daily.mean() * np.sqrt(252)
		c1, c2, c3 = st.columns(3)
		c1.metric("GARCH vol", f"{garch:.1f}%")
		c2.metric("IV", f"{iv:.1f}%" if iv else "n/a")
		c3.metric("Spread", f"{spread:+.1f}%" if iv else "n/a",
          "premium RICH — sell" if spread > 5 else "fair/cheap")