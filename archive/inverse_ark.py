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

def report(df, label):
	fade = df["fade"].sum()
	spysum = df["spy_ret"].sum()
	arkksum = df["arkk_ret"].sum()

	print(f"\n=== {label} ===")
	print(f"fade = {fade}, spy sum: {spysum}, ark sum: {arkksum} ")

def main():
	df = build(5)
	df = fade_returns(df)
	pre = df[df.index < "2023-01-01"]
	post = df[df.index >= "2023-01-01"]
	report(df, "FULL")
	report(pre, "BUST 2021-2022")
	report(post, "RECOVERY 2023-2026")

if __name__ == '__main__':
	main()
