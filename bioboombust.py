import os
import pandas as pd
import requests
import time

from dotenv import load_dotenv
load_dotenv()          # reads .env into environment
API_KEY = os.environ.get("FINNHUB_KEY")

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)


def news_perday(ticker, date, api_key):
	try:
		url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={date}&to={date}&token={api_key}"
		r = requests.get(url)
		data = r.json()
		return len(data)

	except Exception:
		return []

def news_volume(ticker, start, end, api_key):
	counts = []
	dates = pd.date_range(start, end)
	for date in dates:
		counts.append(news_perday(ticker, date.strftime("%Y-%m-%d"), api_key))
	time.sleep(1)
	return pd.Series(counts, index=dates)

def fetch_close(ticker, period="10y"):
	return yf.Ticker(ticker).history(period="10y")["Close"].tz_localize(None)

def build_prices():
	xbi = fetch_close("XBI")
	ibb = fetch_close("IBB")
	spy = fetch_close("SPY")

	df = pd.concat([xbi, ibb, spy], axis=1, sort=True)
	df.columns = ["XBI", "IBB", "SPY"]
	return df.dropna()

def compute_components(df):
	df["XBI_IBB"] = df["XBI"] / df["IBB"]                      # ratio: small-cap vs large-cap
	df["XBI_SPY"] = df["XBI"] / df["SPY"]           # ratio: sector vs market
	df["peak"] = df["XBI"].cummax()           # running all-time high
	df["drawdown"] = (df["XBI"] / df["peak"] - 1) * 100                    # % below that peak
	df["ma200"] = df["XBI"].rolling(200).mean()
	df["vs_ma200"] = (df["XBI"] / df["ma200"] - 1) * 100
	return df                 

def score_components(df):
	recent = df[df.index >= df.index[-1] - pd.DateOffset(years)]
	latest = df.iloc[-1]
	zs = []
	for col in ["XBI_IBB", "XBI_SPY","drawdown", "vs_ma200"]:
		z = (latest[col] - recent[col].mean()) / recent[col].std()
		zs.append(z)
		print(f"{col:8} {latest[col]:+.2f}   z={z:+.2f}")
	score = sum(zs) / len(zs)
	print(f"\nscore: {score:+.2f} (postive = boom-ish, negative = bust-ish)")
	return score


def main():
	df = build_prices()
	df = compute_components(df)
	score_components(df,2)
	score_components(df, 10)
	

if __name__ == '__main__':
	main()

