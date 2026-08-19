import pandas as pd
import requests

def fetch_pageviews(article, start, end):
	url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{article}/daily/{start}/{end}"
	headers = {"User-Agent": "biotech-screen/1.0"}
	r = requests.get(url, headers = headers)
	data = r.json()["items"]

	dates = []
	views = []
	for item in data:
		dates.append(pd.to_datetime(item["timestamp"][:8], format = "%Y%m%d"))
		views.append(item["views"])
	return pd.Series(views, index =dates)

for art in ["Biotechnology", "Moderna", "Ozempic"]:
	s = fetch_pageviews(art, "20240101" , "20260801")
	print(f"{art:20} min {s.min():>7} max{s.max():>7} mean {s.mean():>8.0f}")
