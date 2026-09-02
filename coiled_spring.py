import pandas as pd
import yfinance as yf
import numpy as np


tickers = ["AAPL","NVDA","LLY","GOOGL","MSFT","V","AMD","NVO","MRK","GLW","AVGO","TER"]


def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def coil_score(ticker):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=6)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	closes = df["Close"]
	vol = closes.pct_change().std() * np.sqrt(252) * 100. # annualized vol
	tightness = (closes.max() - closes.min()) / closes.mean() * 100 # range
	return vol, tightness

def screen(tickers):
	results = []
	for tk in tickers:
		ticker_score = coil_score(tk)
		if ticker_score is None:
			continue
		vol, tightness = ticker_score
		coil = vol + tightness
		results.append((tk, vol, tightness, coil))
	results.sort(key=lambda x:x[3])
	return results

	
def main():
	for tk,vol, tightness, coil in screen(tickers):
		print(f"{tk:6} vol {vol:5.1f}%  tight {tightness:5.1f}%  coil {coil:6.1f}")


if __name__ == '__main__':
	main()