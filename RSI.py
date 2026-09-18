import pandas as pd
import yfinance as yf
import sys

DEFAULT_TICKER = "SPY"

def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_closes(ticker, years = 3):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty or len(df) < 400:
		return None
	df = flatten_columns(df)
	closes = df["Close"].dropna() 
	return closes

def rsi(closes, window=14):

	delta = closes.diff()
	gains = delta.clip(lower=0)
	loses = -delta.clip(upper=0)
	avg_gain = gains.rolling(window).mean()
	avg_loss = loses.rolling(window).mean()
	rs = avg_gain /avg_loss
	rsi = 100 - (100 / (1 + rs))
	return rsi.iloc[-1]

def main():
	ticker = sys.argv[1].upper() if len(sys.argv) > 1 else DEFAULT_TICKER
	closes = get_closes(ticker)
	rolling = rsi(closes, 14)
	print(f"{ticker} RSI: {rolling:.1f}")
	if rolling >= 70:
		print("  OVERBOUGHT")
	elif rolling <= 30:
		print("  OVERSOLD")
	else:
		print("  neutral")

if __name__ == '__main__':
	main()
