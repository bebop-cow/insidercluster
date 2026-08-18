import sys
import pandas as pd
try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

def fetch_dxy():
	ticker = "DX-Y.NYB"
	tk = yf.Ticker(ticker)
	last_close = tk.history(period="30y")["Close"]
	return last_close

def fetch_spy():
	ticker = "SPY"
	tk = yf.Ticker(ticker)
	last_close = tk.history(period="30y")["Close"]
	return last_close

def fetch_series(series_id):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	numbers = pd.to_numeric(df[series_id], errors = "coerce")
	return numbers.dropna()

def build_combined():
	thirty = fetch_series("DGS30")
	dxy = fetch_dxy()      # now a series
	spy = fetch_spy()      # now a series
	dxy.index = dxy.index.tz_localize(None)     # strip timezone to match FRED
	spy.index = spy.index.tz_localize(None)
	df = pd.concat([thirty, dxy, spy], axis=1)
	df.columns = ["30Y", "DXY", "SPY"]
	return df.dropna()

def flag_days(df, y30=5.40, dxy_level=99.0):
	yield_ok = df["30Y"] > y30
	dollar_ok = df["DXY"] < dxy_level
	df["flag"] = yield_ok & dollar_ok


	print(f"total days:        {len(df)}")
	print(f"30Y > {y30}:        {yield_ok.sum()}")
	print(f"DXY < {dxy_level}:  {dollar_ok.sum()}")
	print(f"both:              {df['flag'].sum()}")
	return df

def main():
	df = build_combined()
	flag_days(df)


if __name__ == '__main__':
	main()f