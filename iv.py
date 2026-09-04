import math
import pandas as pd
import yfinance as yf

def bs_call_price(S, K, iv, days, r=0.04):
	T = days / 365
	d1 = (math.log(S/K) + (r + iv**2/2) * T) / (iv * math.sqrt(T))
	d2 = d1 - iv * math.sqrt(T)
	N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
	price = S * N(d1) - K * math.exp(-r*T) * N(d2)
	return price

def implied_vol(market_price, S, K, days, r=0.04):
	lo, hi = 0.001, 5.0
	for _ in range(50):
		mid = (lo + hi) / 2
		price = bs_call_price(S, K, mid, days, r)
		if price > market_price:   #priced too high -> vol too high
			hi = mid
		else:
			lo = mid
	return mid

def pick_expiry(tk, min_days=5):
	for exp in tk.options:
		days_to_expiry = (pd.Timestamp(exp) - pd.Timestamp.now()).days
		if days_to_expiry >= min_days:
			return exp
	return tk.options[-1]

def current_atm_iv(ticker):
	tk = yf.Ticker(ticker)
	expiry = pick_expiry(tk, 5)
	calls = tk.option_chain(expiry).calls
	spot = tk.history(period="1d")["Close"].iloc[-1]
	days = (pd.Timestamp(expiry) - pd.Timestamp.now()).days
	calls = calls[(calls["bid"] > 0) & (calls["ask"] > 0)]
	nearest = (calls["strike"] - spot).abs().idxmin()
	row = calls.loc[nearest]
	mid = (row["bid"] + row["ask"]) / 2
	return implied_vol(mid, spot, row["strike"], days)

if __name__ == '__main__':
	main()
