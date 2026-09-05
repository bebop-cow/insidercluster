import pandas as pd
import yfinance as yf

tickers =["V", "CVX", "TER", "CRWV", "AMD", "GOOGL", "NVO", "AAPL", "GLW"]
ticker = "Spy"
def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def days(ticker, days):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(days=days)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	closes = df["Close"]
	return closes

def results(tickers):
	results = []
	for tk in tickers:
		r = days(tk, 7)
		if r is None:
			continue                 # skip bad ticker, keep going
		results.append((tk, r))
	results.sort(key=lambda x: x[1], reverse=True)   # once, after loop
	return results

def main():
	day = results(tickers, 7)
	

if __name__ == '__main__':
	main()