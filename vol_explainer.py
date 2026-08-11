def flag_outliers(ticker, sigma=2.0, top_n=10):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=2)
	
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)

	df["ret"] = df["Close"].pct_change() * 100
	df = df.dropna()
	std = df["ret"].std()
	big = df[df["ret"].abs() > sigma * std]
	biggest_first = big.reindex(big["ret"].abs().sort_values(ascending=False).index)
	

	return biggest_first.head(top_n)