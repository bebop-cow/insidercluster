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
	df = build(12)
	c = same_day_corr(df)
    print(f"USO vs XLE same-day correlation: {c:.2f}")
    
if __name__ == '__main__':
	main()