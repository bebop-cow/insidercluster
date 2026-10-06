import pandas as pd
import yfinance as yf

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def build(month=1):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=month)
	df = yf.download(["XLK","XLF","XLV","XLY","XLP","XLE","XLI","XLB","XLU","XLRE","XLC"], start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	closes = df["Close"]
	pct_change = closes.pct_change() * 100             
	return pct_change.dropna()

def main():
    changes = build(1).tail(20).round(2)
    changes.insert(0, "Day", changes.index.day_name())
    print(changes)

if __name__ == '__main__':
	main()