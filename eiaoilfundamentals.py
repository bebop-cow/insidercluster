import os
from dotenv import load_dotenv
import requests

load_dotenv()

KEY = os.getenv("EIA_KEY")

def get_eia_series(series_id, n=8):
	url = "https://api.eia.gov/v2/series_id/{series_id}"
	params = {
    "api_key": KEY,
	"length": n,          
	}
	r = requests.get(url, params=params, timeout=20)
	rows = r.json()["response"]["data"]
	return [(row["period"], float(row["value"])) for row in rows]

def main():
	print("crude stocks:", get_eia_series("WCESTUS1"))
	print("production:", get_eia_series("WCRFPUS2"))
	# data = get_eia_series("WCESTUS1")
	# latest = data[0][1]
	# prev = data[1][1]
	# change = latest - prev
	# if change < 0:
	# 	print(f"{change} week over week - DRAW(bullish)")
	# else:
	# 	print(f"{change} week over week - BUILD(bearish)")

	# prod = get_eia_series("WCRFPUS2")
	# print("DEBUG prod:", prod)      # is it empty, or an error?
	# prod_now = prod[0][1]
	# prod_prev = prod[1][1]
	# prod_chg = prod_now - prod_prev
	# # rising production = MORE supply = bearish
	# label = "RISING (bearish)" if prod_chg > 0 else "FALLING (bullish)"
	# print(f"Production: {prod_now:,.0f} kbbl/d  ({prod_chg:+,.0f} wk) — {label}")



if __name__ == '__main__':
    	main()    
