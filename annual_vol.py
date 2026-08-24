import numpy as np
import yfinance as yf
import pandas as pd

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def annual_vol(ticker, years = 1):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	ret = df["Close"].pct_change().dropna() * 100
	av = ret.std() * np.sqrt(252) 
	return av


