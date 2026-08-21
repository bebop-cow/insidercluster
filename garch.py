from arch import arch_model
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

DEFAULT_TICKER = "SPY"

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

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

def expected_move_garch(fitted, spot, days=5):
	fc = fitted.forecast(horizon=days)
	total_var = fc.variance.iloc[-1].sum() #variance add
	total_vol = np.sqrt(total_var) #back to % vol over the whole window
	move = spot* total_vol /100
	return move

def fetch_close(ticker, period="10y"):
	return yf.Ticker(ticker).history(period="10y")["Close"].tz_localize(None)

def get_atm_iv(ticker, expiry_index=0):
    tk = yf.Ticker(ticker)
    expiry = tk.options[expiry_index]
    chain = tk.option_chain(expiry)
    calls = chain.calls
    spot = tk.history(period="1d")["Close"].iloc[-1]
    nearest = (calls["strike"] - spot).abs().idxmin()   # index of closest strike
    return calls.loc[nearest, "impliedVolatility"]      


def main():
	ret = get_returns("SPY")
	fitted = fit_garch(ret)
	print(fitted.summary())

	daily = forecast_vol(fitted, 5)
	print("\n forecasted daily vol (%):")
	print(daily)

	spot = fetch_close("SPY").iloc[-1]
	gmove = expected_move_garch(fitted, spot, 5)
	print(f"\nGARCH 5-day expected move: ±${gmove:.2f}  ({gmove/spot*100:.2f}%)")

	iv = get_atm_iv("SPY", 0)          # real ATM IV, nearest expiry
	iv_annual = iv * 100
	garch_annual = daily.mean() * np.sqrt(252)
	print(f"\nIV (annualized):    {iv_annual:.1f}%")
	print(f"GARCH (annualized): {garch_annual:.1f}%")
	print(f"spread (IV - GARCH): {iv_annual - garch_annual:+.1f}%")
	

if __name__ == '__main__':
	main()

