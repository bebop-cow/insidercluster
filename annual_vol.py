import numpy as np
import yfinance as yf

def annual_vol(ticker, years = 1):
	tk = yf.Ticker(ticker)
	last_close = tk.history(period="5d")["Close"].iloc[-1]
	ret = df["Close"].pct_change() * 100
	return ret.dropna()

