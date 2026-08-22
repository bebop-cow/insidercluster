import yfinance as yf
import pandas as pd


DEFAULT_TICKER = "SPY" 

def get_smile(ticker, expiry_index=0):
	tk = yf.Ticker(ticker)
	expiry = tk.options[expiry_index]
	calls = tk.option_chain(expiry).calls
	# keep only the two columns we need
	df = calls[["strike" , "impliedVolatility"]].copy()
	# drop rows where IV is missing or zero (illiquid/junk strikes)
	df = df[df["impliedVolatility"]> 0.001]
	return df, expiry

def main():
	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	df, expiry = get_smile(ticker)
	print(f"expiry {expiry}")
	print(df.to_string())