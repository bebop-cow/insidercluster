import yfinance as yf

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df


def build_data(years=8):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	btc = yf.download("BTC-USD", start=start, end=end, progress=False)
	spy = yf.download("SPY", start=start, end=end, progress=False)
	btc = flatten_columns(btc)["Close"]
	spy = flatten_columns(spy)["Close"]
	btc.index = btc.index.tz_localize(None)
	spy.index = spy.index.tz_localize(None)
	df = pd.concat([btc, spy], axis=1, sort=True)
	df.columns = ["BTC", "SPY"]
	return df.dropna()
	print(build_data().tail())

def main():
	data = build_data(years)

if __name__ == '__main__':
	main()