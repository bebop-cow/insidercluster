from arch import arch_model
import pandas as pd
import numpy as np
from scipy import stats
from iv import current_atm_iv
import sys

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


def rolling_spread(returns, short=5, long=60):
	short_vol = returns.rolling(short).std() * np.sqrt(252)     
	long_vol = returns.rolling(long).std() * np.sqrt(252)     
	spread = short_vol - long_vol
	return spread.dropna()

def spread_zscore(spread):
	z = (spread.iloc[-1] - spread.mean()) / spread.std()
	return z, spread.iloc[-1]

def tail_risk(fitted, spot, days=5, confidence=0.99):
	total_vol = np.sqrt(fitted.forecast(horizon=days).variance.iloc[-1].sum())
	nu = fitted.params["nu"]

	t_crit = stats.t.ppf(confidence, nu)	
	t_move = spot * (t_crit * total_vol / np.sqrt(nu/(nu-2))) / 100

	n_crit = stats.norm.ppf(confidence)
	n_move = spot * (n_crit * total_vol) /100

	return t_move, n_move



def main():
	tickers = [a.upper() for a in sys.argv[1:]] or DEFAULT_TICKERS
	ret = get_returns(tickers)
	fitted = fit_garch(ret)
	print(fitted.summary())

	daily = forecast_vol(fitted, 5)
	print("\n forecasted daily vol (%):")
	print(daily)

	spot = fetch_close(tickers).iloc[-1]
	gmove = expected_move_garch(fitted, spot, 5)
	print(f"\nGARCH 5-day expected move: ±${gmove:.2f}  ({gmove/spot*100:.2f}%)")

	iv = current_atm_iv(tickers)          # real ATM IV, nearest expiry
	iv_annual = iv * 100
	garch_annual = daily.mean() * np.sqrt(252)
	print(f"\nIV (annualized):    {iv_annual:.1f}%")
	print(f"GARCH (annualized): {garch_annual:.1f}%")
	print(f"spread (IV - GARCH): {iv_annual - garch_annual:+.1f}%")

	spread = rolling_spread(ret)
	z, current = spread_zscore(spread)
	print(f"\nvol spread: {current:+.1f}%  z={z:+.2f}")

	t_move, n_move = tail_risk(fitted, spot, 5, 0.99)
	print(f"\n99% worst 5-day move:")
	print(f"  normal model: -${n_move:.2f}")
	print(f"  fat-tail (t): -${t_move:.2f}")
	

if __name__ == '__main__':
	main()

