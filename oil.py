import yfinance as yf
import pandas as pd

def build(months=12):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=months)
	df = yf.download(["USO", "XLE"], start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	closes = df["Close"]              # sub-frame
	return closes.dropna()

def same_day_corr(df):
	rets = df.pct_change().dropna()
	return rets["USO"].corr(rets["XLE"])

def lead_lag(df):
	rets = df.pct_change().dropna()
	xle_next = rets["XLE"].shift(-1)
	return rets["USO"].corr(xle_next)


	 

def main():
	df = build(12)
	c = same_day_corr(df)
	n = lead_lag(df)
	print(f"USO vs XLE same-day correlation: {c:.2f}")
	print(f"USO vs XLE next-day correlation: {n:.2f}")

if __name__ == '__main__':
	main()