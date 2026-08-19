import pandas as pd

def fetch_pageviews(article, start, end):
	url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{article}/daily/{start}/{end}"
	headers = {"User-Agent": "biotech-screen/1.0"}
	r = requests.get(url, headers = headers)
	data = r.json()["items"]

	dates = []
	views = []
	for item in data:
		dates.append(pd.to_datetime(item["timestamp"][:8], format = "%Y%m%d")))
		views.append(item["views"])
	return pd.Series(views, index =dates)

s = fetch_pageviews("Biotechnology", "20240101", "20260801")
print(s.tail())
