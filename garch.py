import arch

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)


def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def get_returns(ticker, years=5):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	ret = df["Close"].pct_change() * 100
	return ret.dropna()


