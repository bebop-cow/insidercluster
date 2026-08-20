import pandas as pd
import requests
import time

from dotenv import load_dotenv
load_dotenv()          # reads .env into environment
API_KEY = os.environ.get("FINNHUB_KEY")

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
	


# def fetch_pageviews(article, start, end):
# 	url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{article}/daily/{start}/{end}"
# 	headers = {"User-Agent": "biotech-screen/1.0"}
# 	r = requests.get(url, headers = headers)
# 	data = r.json()["items"]

# 	dates = []
# 	views = []
# 	for item in data:
# 		dates.append(pd.to_datetime(item["timestamp"][:8], format = "%Y%m%d"))
# 		views.append(item["views"])
# 	return pd.Series(views, index =dates)

# for art in ["Biotechnology", "Moderna", "Ozempic"]:
# 	s = fetch_pageviews(art, "20240101" , "20260801")
# 	print(f"{art:20} min {s.min():>7} max{s.max():>7} mean {s.mean():>8.0f}")

	def main():
		s = news_volume("NVO", "2026-07-01", "2026-07-31", API_KEY)
		print(s)

if __name__ == '__main__':
	main()

