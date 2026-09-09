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

def lead_lag(df, max_lag=5):
    rets = df.pct_change().dropna()
    for lag in range(0, max_lag + 1):
        xle_shifted = rets["XLE"].shift(-lag)
        c = rets["USO"].corr(xle_shifted)
        print(f"lag {lag}d: {c:+.2f}")


def main():
	df = build(12)
	c = same_day_corr(df)
	n = lead_lag(df)
	print(f"USO vs XLE same-day correlation: {c:.2f}")
	

if __name__ == '__main__':
	main()