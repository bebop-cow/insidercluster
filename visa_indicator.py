import pandas as pd
import yfinance as yf

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def build(years=5):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(["V", "QQQ"], start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	closes = df["Close"]              # sub-frame: QQQ and V columns
	return closes.dropna()
	
def fade_returns(df):
	df["v_ret"] = df["V"].pct_change() * 100
	df["qqq_ret"] = df["qqq"].pct_change() * 100
	df["fade"] = df["qqq_ret"] - df["v_ret"]
	return df

def report(df, label):
	fade = df["fade"].sum()
	vsum = df["v_ret"].sum()
	qqqsum = df["qqq_ret"].sum()

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