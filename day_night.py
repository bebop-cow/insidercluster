import sys
import pandas as pd
import yfinance as yf

DEFAULT_TICKER = "SPY"

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def get_ohlc(ticker, years=5):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	return df[["Open", "Close"]].dropna()

def split_returns(df):
	df["overnight"] = (df["Open"] / df["Close"].shift(1)-1) * 100
	df["intraday"] = (df["Close"] / df["Open"]-1) * 100
	return df

def compare(df, ticker):
	avg_overnight = df["overnight"].mean()
	avg_intraday = df["intraday"].mean()
	print(f"{ticker} avg overnight move {avg_overnight} ,  avg intraday move {avg_intraday}")

	tot_overnight = df["overnight"].sum()
	tot_intraday = df["intraday"].sum()
	print(f"        total overnight {tot_overnight:+.1f}%   total intraday {tot_intraday:+.1f}%")

def main():
	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	df = get_ohlc(ticker, 5)
	df = split_returns(df)
	compare(df,ticker)

if __name__ == '__main__':
	main()
