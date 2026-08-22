import sys
import yfinance as yf
import pandas as pd
import math

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Run: pip install matplotlib")
    sys.exit(1)


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
	df = df[(df["strike"] >= lo) & (df["strike"] <= hi)]
	# drop rows where IV is missing or zero (illiquid/junk strikes)
	df = df[df["impliedVolatility"]> 0.001]
	return df, expiry, last_close

def call_delta(S, K, iv, days, r=0.04):
	T = days / 365
	d1 = (math.log(S/K) + (r + iv**2/2) * T) / (iv * math.sqrt(T))
	delta = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
	return delta

def add_delta(df, spot, days):
	deltas = []
	for row in df.itertuples():
		d = call_delta(spot, row.strike, row.impliedVolatility, days)
		deltas.append(d)
	df["delta"] = deltas
	return df

def plot_delta(df, spot):
	plt.plot(df["strike"], df["delta"], marker="o")
	plt.axvline(spot, color="red", linestyle="--")
	plt.axhline(0.5, color="gray", linestyle=":")   # the coin-flip line
	plt.xlabel("strike")
	plt.ylabel("delta")
	plt.title("AMD delta by strike")
	plt.show()

def plot_smile(df, expiry, spot):
	plt.plot(df["strike"], df["impliedVolatility"] * 100, marker="o")
	plt.axvline(spot, color="red", linestyle="--")
	plt.xlabel("strike")
	plt.ylabel("IV %")
	plt.title(f"AMD smile - {expiry}")
	plt.show()

def main():
	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	df, expiry, spot = get_smile(ticker)
	days = (pd.Timestamp(expiry) - pd.Timestamp.now()).days
	delta = add_delta(df, spot, days)
	print(f"expiry {expiry}")
	print(df.to_string())
	plot_smile(df, expiry, spot)
	plot_delta(df, spot)

if __name__ == '__main__':
	main()