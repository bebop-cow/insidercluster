def fetch_series(series_id):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	numbers = pd.to_numeric(df[series_id], errors = "coerce")
	return numbers.dropna()

def build_curve():
	twoy = fetch_series("DGS2")
	teny = fetch_series("DGS10")
	thirtyy = fetch_series("DGS30")

	df = pd.concat([twoy, teny, thirtyy], axis=1)
	df.columns = ["2Y", "10Y", "30Y"]
	return df.dropna()

def compute_spreads(df):
	df["2s10s"] = df["10Y"] - df["2Y"]
	df["10s30s"] = df["30Y"] - df["10Y"]
	df["fly"] = 2 * df["10Y"] - (df["2Y"] + df["30Y"])

	return df

def main():
    curve = build_curve()
    spreads = compute_spreads(curve)
    latest = spreads.iloc[-1]          # last row = most recent date

    print(f"as of {spreads.index[-1].date()}\n")
    for col in ["2Y", "10Y", "30Y"]:
        print(f"{col:8} {latest[col]:.2f}%")
    print()
    for col in ["2s10s", "10s30s", "fly"]:
        z = (latest[col] - spreads[col].mean()) / spreads[col].std()
        print(f"{col:8} {latest[col]:+.2f}   z={z:+.2f}")

if __name__ == '__main__':
	main()

	