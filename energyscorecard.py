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

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def rel_strength(ticker, months=3):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=months)
	df = yf.download([ticker,"SPY"], start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	closes = df["Close"].dropna() 
	tk_ret = (closes[ticker].iloc[-1]/closes[ticker].iloc[0]-1) * 100            
	spy_ret = (closes["SPY"].iloc[-1]/closes["SPY"].iloc[0]-1) * 100            
	return tk_ret - spy_ret

def scorecard():
	sectors = {"Oil": "XLE", "Solar": "TAN", "Nuclear": "URA"}
	for name, tk in sectors.items():
		rs = rel_strength(tk)
		closes = yf.Ticker(tk).history(period="5y")["Close"].dropna()
		ma50 = closes.rolling(50).mean().iloc[-1]
		yoy = closes.rolling(365).mean().iloc[-1]
		y5 = closes.rolling(1250).mean().iloc[-1]
		ma50trend = "above 50d (uptrend)" if closes.iloc[-1] > ma50 else "below 50d (downtrend)"
		yoytrend = "above yoy (uptrend)" if closes.iloc[-1] > yoy else "below yoy (downtrend)"
		y5trend = "above y5 (uptrend)" if closes.iloc[-1] > y5 else "below y5 (downtrend)"
		print(f"{name:8} ({tk}): RS vs SPY {rs:+.1f}% · {ma50trend} · {yoytrend} · {y5trend}")

def main():
	stocks =  get_eia_series("WCESTUS1", "stoc/wstk")
	prod = get_eia_series("WCRFPUS2", "sum/sndw")
	spr =  get_eia_series("WCSSTUS1", "sum/sndw")
	gasd = get_eia_series("WGFUPUS2", "sum/sndw")
	stock_chg = stocks[0][1] - stocks[4][1]      # draw/build
	prod_chg = prod[0][1] - prod[4][1]           # supply direction
	spr_chg = spr[0][1] - spr[4][1]           # spr direction
	gasd_chg = gasd[0][1] - gasd[4][1]           # gasoline demand direction
	# print(f"Inventories: {stock_chg:+,.0f}k — {'DRAW (bullish)' if stock_chg<0 else 'BUILD (bearish)'}")
	# print(f"Production:  {prod_chg:+,.0f}k/d — {'RISING (bearish)' if prod_chg>0 else 'FALLING (bullish)'}")
	# print(f"SPR:  {spr_chg:+,.0f}k/d — {'RELEASING (bearish)' if spr_chg<0 else 'REFILLING (bullish)'}")
	# print(f"GASOLINE demand:  {gasd_chg:+,.0f}k/d — {'RISING (bullish)' if gasd_chg>0 else 'FALLING (bearish)'}")
	score = scorecard()


if __name__ == '__main__':
    	main()    
