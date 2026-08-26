import yfinance as yf
import pandas as pd

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

def flag_rallies(df):
	df["bct_5d"] = df["BTC"].pct_change(5) * 100
	df["rally"] =  df["bct_5d"] > 10 
	return df
	
def forward_returns(df):
	df["fwd5"] = df["SPY"].pct_change(5).shift(-5) * 100
	df["fwd10"] = df["SPY"].pct_change(10).shift(-10) * 100
	df["fwd20"] = df["SPY"].pct_change(20).shift(-20) * 100
	return df

def comparison(df, label):
	rallies = df[df["rally"]]
	count = df["rally"].sum()
	print(f"\n=== {label} ===")
	print(f"BTC rallies (>10% in 5d): n={count}\n")

	for h in ["fwd5", "fwd10", "fwd20"]:
		rally_avg = rallies[h].mean()
		base_avg = df[h].mean()
		print(f"{h}:  rally {rally_avg:+.2f}%   baseline {base_avg:+.2f}%")
	


def main():
	df = build_data(8)
	flag = flag_rallies(df)
	forward = forward_returns(df)
	# compare = comparison(df, label)

	predf = df[df.index < "2022-01-01"]
	postdf = df[df.index >= "2022-01-01"]
	

	full = comparison(df, "full")
	pre = comparison(predf, "pre") 
	post = comparison(postdf, "post")
	

if __name__ == '__main__':
	main()