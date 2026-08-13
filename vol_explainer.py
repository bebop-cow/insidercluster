import sys
import requests
import pandas as pd
import os

from dotenv import load_dotenv
load_dotenv()          # reads .env into environment
API_KEY = os.environ.get("FINNHUB_KEY")

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)


DEFAULT_TICKER = "SPY"

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

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

def get_news(ticker, limit=5):
	try:
		tk = yf.Ticker(ticker)
		items = tk.news[:limit]
		out = []
	
		for it in items:
			c = it.get("content", {})
			title = c.get("title", "?")
			date = c.get("pubDate", "?")
			out.append((date, title))
		return out
	except Exception:
		return []

def news_for_date(ticker, date, api_key, limit=3):
	try:
		url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={date}&to={date}&token={api_key}"
		r = requests.get(url)
		data = r.json()
		out = []
		for item in data[:limit]:
			out.append(item["headline"])
		return out

	except Exception:
		return []
	


def main():

	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	outlier = flag_outliers(ticker)
	print(f"\n{ticker} - biggest moves:")
	print(outlier[["Close", "ret"]])

	print(f"\n recent news:")
	for date in outlier.index:
		ds = date.strftime("%Y-%m-%d")
		move = outlier.loc[date, "ret"]
		print(f"\n{ds}  {move:+.2f}%")
		heads = news_for_date(ticker, ds, API_KEY)
		if not heads:
			print("   (no news — outside free-tier history)")
		for h in heads:
			print(f"   · {h}")

if __name__ == '__main__':
	main()

	
