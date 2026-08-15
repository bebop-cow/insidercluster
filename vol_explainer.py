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
	start = end - pd.DateOffset(years=1)
	
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

def news_for_date(ticker, date, api_key, limit=6):
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

def rank_headlines(headlines, ticker, company):
	score = lambda h: 1 if (ticker.lower() in h.lower() or company.lower() in h.lower()) else 0 
	return sorted(headlines, key=score, reverse=True)

def score(h):
    hl = h.lower()
    s = 0
    if ticker.lower() in hl or company.lower() in hl:
        s += 2
    if any(w in hl for w in ["why", "soar", "jump", "plunge", "downgrade", "upgrade", "earnings", "fda", "approv"]):
        s += 1
    if "recap" in hl or "roundup" in hl or "stocks to watch" in hl:
        s -= 1        # penalize list articles
    return s
	
def main():

	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	outlier = flag_outliers(ticker)
	print(f"\n{ticker} - biggest moves:")
	print(outlier[["Close", "ret"]])
	COMPANIES = {"LLY": "Eli Lilly", "NVO": "Novo Nordisk", "AMD": "AMD", "SPY": "S&P"}
	COMPANY = COMPANIES.get(ticker, ticker) 

	
	for date in outlier.index:
		ds = date.strftime("%Y-%m-%d")
		move = outlier.loc[date, "ret"]
		print(f"\n{ds}  {move:+.2f}%")
		heads = news_for_date(ticker, ds, API_KEY)
		heads = rank_headlines(heads, ticker, COMPANY)
		if not heads:
			print("   (no news — outside free-tier history)")
		for h in heads:
			print(f"   · {h}")

if __name__ == '__main__':
	main()

	
