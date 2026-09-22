import os
from dotenv import load_dotenv
import requests
import yfinance as yf
import pandas as pd

load_dotenv()

KEY = os.getenv("EIA_KEY")

def get_eia_series(series_id,route, n=8):
	url = f"https://api.eia.gov/v2/petroleum/{route}/data/"
	params = {
        "api_key": KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": series_id,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": n,
    }
	r = requests.get(url, params=params, timeout=20)
	rows = r.json()["response"]["data"]
	return [(row["period"], float(row["value"])) for row in rows]

def rel_strength(ticker, months=3):


def main():
	stocks =  get_eia_series("WCESTUS1", "stoc/wstk")
	prod = get_eia_series("WCRFPUS2", "sum/sndw")
	spr =  get_eia_series("WCSSTUS1", "sum/sndw")
	gasd = get_eia_series("WGFUPUS2", "sum/sndw")
	stock_chg = stocks[0][1] - stocks[4][1]      # draw/build
	prod_chg = prod[0][1] - prod[4][1]           # supply direction
	spr_chg = spr[0][1] - spr[4][1]           # spr direction
	gasd_chg = gasd[0][1] - gasd[4][1]           # gasoline demand direction
	print(f"Inventories: {stock_chg:+,.0f}k — {'DRAW (bullish)' if stock_chg<0 else 'BUILD (bearish)'}")
	print(f"Production:  {prod_chg:+,.0f}k/d — {'RISING (bearish)' if prod_chg>0 else 'FALLING (bullish)'}")
	print(f"SPR:  {spr_chg:+,.0f}k/d — {'RELEASING (bearish)' if spr_chg<0 else 'REFILLING (bullish)'}")
	print(f"GASOLINE demand:  {gasd_chg:+,.0f}k/d — {'RISING (bullish)' if gasd_chg>0 else 'FALLING (bearish)'}")


if __name__ == '__main__':
    	main()    
