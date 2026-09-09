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
	spy = fetch_close("SPY")
	spy.index = spy.index.tz_localize(None)
	df = pd.concat([teny,spy], axis=1, sort=True)
	df.columns = ["y10", "SPY"]
	return df.dropna()

def flag_regime(df, window=100):
	ma = df["y10"].rolling(window).mean()
	df["rising"] = df["y10"] > ma
	return df

def forward_returns(df, days=63):
	df["fwd"] = df["SPY"].pct_change(days).shift(-days) * 100
	return df

def compare(df,days):
	rising = df[df["rising"]]["fwd"].dropna()
	falling = df[~df["rising"]]["fwd"].dropna()
	print(f"RISING rates:  {rising.mean():+.2f}%  (n={len(rising)})")
	print(f"FALLING rates: {falling.mean():+.2f}%  (n={len(falling)})")

def main():
    df = build(20)
    df = flag_regime(df)
    df = forward_returns(df, 63)
    print("=== FULL ===");  compare(df, 63)
    print("=== pre-2020 ==="); compare(df[df.index < "2020-01-01"], 63)
    print("=== 2020+ ===");   compare(df[df.index >= "2020-01-01"], 63)

if __name__ == "__main__":
    main()
