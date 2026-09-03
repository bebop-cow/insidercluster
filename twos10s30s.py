import sys
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Run: pip install matplotlib")
    sys.exit(1)

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

def fetch_series(series_id):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	numbers = pd.to_numeric(df[series_id], errors = "coerce")
	return numbers.dropna()

def build_curve():
	twoy = fetch_series("DGS2")
	teny = fetch_series("DGS10")
	thirtyy = fetch_series("DGS30")

	df = pd.concat([twoy, teny, thirtyy], axis=1, sort=True)
	df.columns = ["2Y", "10Y", "30Y"]
	return df.dropna()

def compute_spreads(df):
	df["2s10s"] = df["10Y"] - df["2Y"]
	df["10s30s"] = df["30Y"] - df["10Y"]
	df["2s30s"] = df["30Y"] - df["2Y"]
	df["fly"] = 2 * df["10Y"] - (df["2Y"] + df["30Y"])

	return df

def fetch_dxy():
	ticker = "DX-Y.NYB"
	tk = yf.Ticker(ticker)
	last_close = tk.history(period="5d")["Close"].iloc[-1]
	return last_close

def fetch_dxy_history(period="1y"):
	ticker = "DX-Y.NYB"
	tk = yf.Ticker(ticker)
	last_close = tk.history(period)["Close"]
	return last_close

def fetch_live():
	ticker = "^TYX"
	tk = yf.Ticker(ticker)
	return tk.history(period="5d")["Close"].iloc[-1]

def fetcj_jgb():
	return fetch_series("IRLTLT01JPM156N")
	
def check_conditions(dxy, y30, dxy_level=99.0, y30_level=5.40):
	a = dxy < dxy_level
	b = y30 > y30_level
	print(f"DXY  {dxy:.2f}  vs {dxy_level}  gap {dxy - dxy_level:+.2f}   {'MET' if a else 'not met'}")
	print(f"30Y  {y30:.2f}% vs {y30_level}% gap {y30 - y30_level:+.2f}   {'MET' if b else 'not met'}")
	print(f"\nboth conditions: {'YES' if (a and b) else 'no'}")

def sparkline(series, width = 10):
	BLOCKS = "▁▂▃▄▅▆▇█"
	vals = series.tail(width).tolist()
	lo, hi = min(vals), max(vals)
	if hi == lo:
		return BLOCKS[0] * len(vals)
	chars = []
	for v in vals:
		idx = int((v - lo) / (hi - lo) * 7)
		chars.append(BLOCKS[idx])
	return "".join(chars)

def plot_curve(spreads, dxy_hist):
	cutoff = pd.Timestamp.now() - pd.DateOffset(years=1)
	s = spreads[spreads.index >= cutoff]
	fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

	ax1.plot(s.index, s["30Y"])
	ax1.axhline(5.40, color="red", linestyle="--")
	ax1.set_ylabel("30Y %")

	ax2.plot(dxy_hist.index, dxy_hist.values, color="orange")
	ax2.axhline(99.0, color="red", linestyle="--")
	ax2.set_ylabel("DXY")
	plt.tight_layout()
	plt.show()

	
def main():
	want_chart = "--chart" in sys.argv
	curve = build_curve()
	spreads = compute_spreads(curve)
	latest = spreads.iloc[-1]          # last row = most recent date
	live30 = fetch_live()
	fred30 = latest["30Y"]
	delta = live30 - fred30
	dxy_hist = fetch_dxy_history()
	print(f"\n30Y  FRED {fred30:.2f}% (as of {spreads.index[-1].date()})")
	print(f"30Y  live {live30:.2f}%   move since: {delta:+.2f}")
    
	for col in ["2Y", "10Y", "30Y"]:
		print(f"{col:8} {latest[col]:.2f}%")
	print()
	cutoff = pd.Timestamp.now() - pd.DateOffset(years=1)
	recent = spreads[spreads.index >= cutoff]
	for col in ["2s10s", "10s30s","2s30s", "fly"]:
		z = (latest[col] - recent[col].mean()) / recent[col].std()
		print(f"{col:8} {latest[col]:+.2f}   z={z:+.2f}")

	dxy = fetch_dxy()
	check_conditions(dxy, live30)

	jgp = fetcj_jgb()


	print(f"\n30Y  {live30:.2f}%  {sparkline(spreads['30Y'])}  trigger 5.40  gap {live30-5.40:+.2f}")
	print(f"DXY  {dxy:.2f}   {sparkline(dxy_hist)}  trigger 99.0  gap {dxy-99.0:+.2f}")

	print(f"\njgb {jgb:.2f}%")

	if want_chart:
		plot_curve(spreads, dxy_hist)
	

if __name__ == '__main__':
	main()

	