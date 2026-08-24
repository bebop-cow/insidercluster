import numpy as np
import yfinance as yf
import pandas as pd

tickers = ["AAPL","NVDA","LLY","GOOGL","MSFT","V","AMD","NVO","MRK","GLW","AVGO","TER"]

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

def results_table(tickers):
	results = []
	for tk in tickers:
		r = annual_vol(tk, 1)
		if r is None:
			continue                 # skip bad ticker, keep going
		results.append((tk, r))
	results.sort(key=lambda x: x[1], reverse=True)   # once, after loop
	for tk, vol in results:
		print(f"{tk:6} {vol:5.1f}%")

def main():
	table = results_table(tickers)

if __name__ == '__main__':
	main()
