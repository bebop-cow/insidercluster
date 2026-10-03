import yfinance as yf
import pandas as pd

def project_fcf(fcf0, growth, years=5):
	projectfcf = []
	for yr in range(1, years+1):
		year_n = fcf0 * (1 + growth)**yr
		projectfcf.append(year_n)
	return projectfcf

def discount_to_pv(cashflows, discount_rate):
	pvs = []
	for i, cf in enumerate(cashflows):
		year = i + 1                              # index 0 = year 1
		pv = cf / (1 + discount_rate)**year
		pvs.append(pv)
	return pvs

def terminal_value(last_fcf, terminal_growth, discount_rate):
	tv = last_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
	if terminal_growth >= discount_rate:
		return None
	return tv

def intrinsic_value(fcf0, growth, discount_rate, terminal_growth, shares, years=5):
	cfs = project_fcf(fcf0, growth, years)
	pvs = discount_to_pv(cfs, discount_rate)
	tv = terminal_value(cfs[-1], terminal_growth, discount_rate)
	tv_pv = tv / (1 + discount_rate)**years
	total = sum(pvs) + tv_pv
	return total / shares

def reverse_dcf(price, fcf0, discount_rate, terminal_growth, shares, years=5):
	lo, hi = -0.10,0.50
	for _ in range(50):
		mid = (lo + hi) / 2
		iv = intrinsic_value(fcf0, mid, discount_rate, terminal_growth, shares, years)
		if iv > price:
			hi = mid
		else:
			lo = mid
	return mid

def market_implied_growth(tk, discount_rate=0.10, terminal_growth=0.025):
	price = yf.Ticker(tk).history(period="1d")["Close"].iloc[-1]
	shares = yf.Ticker(tk).info.get("sharesOutstanding")
	fcf_row = yf.Ticker(tk).cashflow.loc["Free Cash Flow"]
	fcf = fcf_row.iloc[:4].mean()
	if not shares or pd.isna(fcf) or fcf <= 0:
		return None      # DCF meaningless without positive FCF + shares

	rd = reverse_dcf(price, fcf,discount_rate, terminal_growth, shares)
	if rd is None or rd > 0.40 or rd < -0.05:
		return None      # implausible — likely bad FCF data
	return rd * 100

print(market_implied_growth("XOM", 0.10, 0.025))