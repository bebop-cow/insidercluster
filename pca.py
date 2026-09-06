import pandas as pd
import yfinance as yf
from openpyxl.workbook import Workbook

tickers =["V", "CVX", "TER", "CRWV", "AMD", "GOOGL", "NVO", "AAPL", "GLW"]
def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def days(ticker, n):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(days=n*2 + 10)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	closes = df["Close"].tail(n)
	return closes

def results(tickers, n=7):
	data ={}
	for tk in tickers:
		r = days(tk, n)
		if r is None:
			continue                 # skip bad ticker, keep going
		data[tk] = r
	return pd.DataFrame(data)

def main():
	df = results(tickers,7)
	print(df)
	print(df.shape)
	df.to_excel("closes.xlsx")
	print("wrote closes.xlsx")
	

if __name__ == '__main__':
	main()