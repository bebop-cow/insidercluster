import math

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

p = bs_call_price(100, 100, 0.20, 30)   # price at 20% vol
print(implied_vol(p, 100, 100, 30))     # should recover ~0.20
