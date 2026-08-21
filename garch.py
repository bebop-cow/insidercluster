from arch import arch_model

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

def fit_garch(returns):
	model = arch_model(returns, vol="Garch", p=1, q=1, mean="Constant", dist="normal")
	fitted = model.fit(disp="off")
	return fitted

def main():
	ret = get_returns("SPY")
	fitted = fit_garch(ret)
	print(fitted.summary())

if __name__ == '__main__':
	main()

