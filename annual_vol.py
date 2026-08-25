import numpy as np
import yfinance as yf
import pandas as pd
from arch import arch_model

tickers = ["AAPL","NVDA","LLY","GOOGL","MSFT","V","AMD","NVO","MRK","GLW","AVGO","TER"]

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def annual_vol(ticker, years = 1):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	ret = df["Close"].pct_change().dropna() * 100
	av = ret.std() * np.sqrt(252) 
	return av

def results_table(tickers):
	results = []
	for tk in tickers:
		r = annual_vol(tk, 1)
		if r is None:
			continue                 # skip bad ticker, keep going
		results.append((tk, r))
	results.sort(key=lambda x: x[1], reverse=True)   # once, after loop
	for tk, vol in results:
		print(f"{tk:6} {vol:5.1f}%")

def get_returns(ticker, years=5):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	ret = df["Close"].pct_change() * 100
	return ret.dropna()

def fit_garch(returns):
	model = arch_model(returns, vol="Garch", p=1, q=1, mean="Constant", dist="t")
	fitted = model.fit(disp="off")
	return fitted

def forecast_vol(fitted, days=5):
	fc = fitted.forecast(horizon=days)
	variances = fc.variance.iloc[-1] #forecasted variance per day ahead
	daily_vol = np.sqrt(variances) #variance -> std dev (daily vol %)
	return daily_vol

def pick_expiry(tk, min_days=5):
	for exp in tk.options:
		days_to_expiry = (pd.Timestamp(exp) - pd.Timestamp.now()).days
		if days_to_expiry >= min_days:
			return exp
	return tk.options[-1]

def get_atm_iv(ticker, expiry_index=0):
	tk = yf.Ticker(ticker)
	expiry = pick_expiry(tk, 5)
	chain = tk.option_chain(expiry)
	calls = chain.calls
	spot = tk.history(period="1d")["Close"].iloc[-1]
	print("expiry:", expiry, "spot:", round(spot,2))
	near = calls[(calls["strike"] > spot*0.9) & (calls["strike"] < spot*1.1)]
	print(near[["strike","impliedVolatility","volume","lastPrice"]].to_string())
	calls = calls[calls["impliedVolatility"] > 0.01]
	nearest = (calls["strike"] - spot).abs().idxmin()


	return calls.loc[nearest, "impliedVolatility"]          # that row's IV

def vol_signal(ticker):
	realized = annual_vol(ticker, 1)

	ret = get_returns(ticker)
	fitted = fit_garch(ret)
	daily = forecast_vol(fitted, 5)
	garch_annual = daily.mean() * np.sqrt(252) # annualize the daily forecast

	iv = get_atm_iv(ticker) * 100

	spread = iv - garch_annual
	return realized, garch_annual, iv, spread

def main():
	realized, garch, iv, spread = vol_signal("NVO")
	print(f"NVO  realized {realized:.1f}%  GARCH {garch:.1f}%  IV {iv:.1f}%  spread {spread:+.1f}%")

if __name__ == '__main__':
	main()
