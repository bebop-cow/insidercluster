import pandas as pd

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

def check_conditions(dxy, y30, dxy_level=99.0, y30_level=5.40):
	a = dxy < dxy_level
	b = y30 > y30_level
	print(f"DXY  {dxy:.2f}  vs {dxy_level}  gap {dxy - dxy_level:+.2f}   {'MET' if a else 'not met'}")
	print(f"30Y  {y30:.2f}% vs {y30_level}% gap {y30 - y30_level:+.2f}   {'MET' if b else 'not met'}")
	print(f"\nboth conditions: {'YES' if (a and b) else 'no'}")

def main():
    curve = build_curve()
    spreads = compute_spreads(curve)
    latest = spreads.iloc[-1]          # last row = most recent date
    dxy = fetch_dxy()
    check_conditions(dxy, latest["30Y"])

    print(f"as of {spreads.index[-1].date()}\n")
    for col in ["2Y", "10Y", "30Y"]:
        print(f"{col:8} {latest[col]:.2f}%")
    print()
    for col in ["2s10s", "10s30s","2s30s", "fly"]:
        z = (latest[col] - spreads[col].mean()) / spreads[col].std()
        print(f"{col:8} {latest[col]:+.2f}   z={z:+.2f}")



if __name__ == '__main__':
	main()

	