import yfinance as yf
import pandas as pd


def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def get_closes(ticker, months = 6):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=months)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	closes = df["Close"].dropna() 
	return closes

def basket_performance(tickers, months=6):
	results = []
	for tk in tickers:
		performance = get_closes(tk, months)
		if performance is None:
			continue
		closes = performance
		ret = (closes.iloc[-1] / closes.iloc[0] - 1) * 100
		results.append((tk, ret))
	return results

ef main():
    tickers = ["PG", "PEP", "WMT", "COST", "KO", "CAT", "FDX"]
    perf = basket_performance(tickers, 6)

    # basket average
    basket_avg = sum(r for _, r in perf) / len(perf)

    # SPY benchmark — same return calc
    spy = get_closes("SPY", 6)
    spy_ret = (spy.iloc[-1] / spy.iloc[0] - 1) * 100

    # print each name
    for tk, r in perf:
        print(f"{tk:6} {r:+.1f}%")
    print(f"\nbasket avg: {basket_avg:+.1f}%")
    print(f"SPY:        {spy_ret:+.1f}%")
    print(f"basket - SPY: {basket_avg - spy_ret:+.1f}%   (positive = defensive outperforming = risk-off tell)")

if __name__ == '__main__':
	main()


