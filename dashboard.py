import streamlit as st
import pandas as pd
import numpy as np

from garch import get_returns, fit_garch, forecast_vol, tail_risk, fetch_close
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