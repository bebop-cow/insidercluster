import sys
import yfinance as yf
import pandas as pd


DEFAULT_TICKER = "SPY" 

def get_smile(ticker, expiry_index=0):
	tk = yf.Ticker(ticker)
	last_close = tk.history(period="1d")["Close"].iloc[-1]
	lo = last_close * 0.95
	hi = last_close * 1.10
	expiry = tk.options[expiry_index]
	calls = tk.option_chain(expiry).calls
	# keep only the two columns we need
	df = calls[["strike" , "impliedVolatility"]].copy()
	df = df[(df["strike"] >= lo) & (df["strike" <= hi])]
	# drop rows where IV is missing or zero (illiquid/junk strikes)
	df = df[df["impliedVolatility"]> 0.001]
	return df, expiry


def main():
	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	df, expiry = get_smile(ticker)
	print(f"expiry {expiry}")
	print(df.to_string())

if __name__ == '__main__':
	main()