import pandas as pd
import yfinance as yf

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def build(years=5):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(["ARKK", "SPY"], start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	closes = df["Close"]              # sub-frame: ARKK and SPY columns
	return closes.dropna()
	
def fade_returns(df):
	df["arkk_ret"] = df["ARKK"].pct_change() * 100
	df["spy_ret"] = df["SPY"].pct_change() * 100
	df["fade"] = df["spy_ret"] - df["arkk_ret"]
	return df

def main():
	inverse = build(5)
	fade_returns(inverse)

if __name__ == '__main__':
	main()
