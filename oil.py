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
	 

def main():
	corr = build(12)
	df = same_day_corr(corr)
	print(f"Correlation between the two {df}")

if __name__ == '__main__':
	main()