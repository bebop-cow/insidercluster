import pandas as pd
import yfinance as yf
import numpy as np


def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def coil_score(ticker):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=6)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	closes = df["Close"]
	vol = closes.pct_change().std() * np.sqrt(252) * 100. # annualized vol
	tightness = (closes.max() - closes.min()) / closes.mean() * 100 # range
	return vol, tightness
	
def main():
	vol,tightness = coil_score("AMD")
	print(f"AMD  vol {vol:.1f}%  tightness {tightness:.1f}%")


if __name__ == '__main__':
	main()