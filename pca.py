import pandas as pd
import yfinance as yf
from openpyxl.workbook import Workbook

tickers =["TAN","PBW", "FAN", "NLR"]
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

def results(tickers, n=6):
	data ={}
	for tk in tickers:
		r = days(tk, n)
		if r is None:
			continue                 # skip bad ticker, keep going
		data[tk] = r
	return pd.DataFrame(data)

def main():
	df = results(tickers,1500)
	print(df)
	print(df.shape)
	df.to_excel("nonoil.xlsx")
	print("wrote nonoil.xlsx")
	

if __name__ == '__main__':
	main()