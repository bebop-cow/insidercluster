DEFAULT_TICKER = "SPY"


	

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def get_ohlc(ticker, years=5):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	return df[["Open", "Close"]].dropna()

def split_returns(df):
	df["overnight"] = (df["Open"] / df["Close"].shift(1)-1) * 100
	df["intraday"] = (df["Close"] / df["Open"]-1) * 100
	return df
