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

def call_gamma(S, K, iv, days, r=0.04):
	T = days / 365
	d1 = (math.log(S/K) + (r + iv**2/2) * T) / (iv * math.sqrt(T))
	pdf = math.exp(-d1**2 / 2) / math.sqrt(2 * math.pi)         # normal PDF at d1
	gamma = pdf / (S * iv * math.sqrt(T))
	return gamma

def add_gamma(df, spot, days):
	gammas = []
	for row in df.itertuples():
		g = call_gamma(spot, row.strike, row.impliedVolatility, days)
		gammas.append(g)
	df["gamma"] = gammas
	return df

def plot_greeks(df, spot):
	fig, ax1 = plt.subplots()

	ax1.plot(df["strike"], df["delta"], marker="o", color="blue", label="delta")
	ax1.axvline(spot, color="red", linestyle="--")
	ax1.set_xlabel("strike")
	ax1.set_ylabel("delta", color="blue")

	ax2 = ax1.twinx()                    # second y-axis sharing the x
	ax2.plot(df["strike"], df["gamma"], marker="s", color="green", label="gamma")
	ax2.set_ylabel("gamma", color="green")

	plt.title("AMD delta & gamma by strike")
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
	want_chart = "--chart" in sys.argv
	df, expiry, spot = get_smile(ticker)
	days = (pd.Timestamp(expiry) - pd.Timestamp.now()).days
	delta = add_delta(df, spot, days)
	gamma = add_gamma(df, spot, days)
	print(f"expiry {expiry}")
	print(df.to_string())
	if want_chart:
		plot_smile(df, expiry, spot)
		plot_greeks(df, spot)

if __name__ == '__main__':
	main()