import os
from dotenv import load_dotenv
import requests

load_dotenv()

KEY = os.getenv("EIA_KEY")

def get_eia_series(series_id, n=80):
	url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
	params = {
    "api_key": KEY,
	"frequency": "weekly",
	"data[0]": "value",
	"facets[series][]": series_id, 
	"sort[0][column]": "period",
	"sort[0][direction]": "desc",
	"length": 5,          # just the 5 most recent
	}
	r = requests.get(url, params=params, timeout=20)
	rows = r.json()["response"]["data"]
	return [(row["period"], float(row["value"])) for row in rows]

def main():
	data = get_eia_series("WCESTUS1")
	latest = data[0][1]
	prev = data[1][1]
	change = latest - prev
	if change < 0:
		print(f"{change} week over week - DRAW(bullish)")
	else:
		print(f"{change} week over week - BUILD(bearish)")



if __name__ == '__main__':
    	main()    
