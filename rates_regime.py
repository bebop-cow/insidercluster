import yfinance as yf
import pandas as pd


def fetch_series(series_id):
	url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
	df = pd.read_csv(url, parse_dates=["observation_date"], index_col = "observation_date")
	numbers = pd.to_numeric(df[series_id], errors = "coerce")
	return numbers.dropna()

def fetch_close(ticker, period="20y"):
	return yf.Ticker(ticker).history(period=period)["Close"].tz_localize(None)

def build(years=20):
	teny = fetch_series("DGS10")
	ticker = fetch_close("SPY")
	spy.index = spy.index.tz_localize(None)
	df = pd.concat([teny,spy], axis=1, sort=True)
	df.columns = ["y10", "SPY"]
	return df.dropna()


def main():
	print(build().tail())

if __name__ == '__main__':
	main()
