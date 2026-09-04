import pandas as pd
import yfinance as yf

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def build(months=3):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(months=months)
	df = yf.download(["V", "QQQ"], start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	closes = df["Close"]              # sub-frame: QQQ and V columns
	return closes.dropna()
	
def test_leadlag(df):
	df["v_ret"] = df["V"].pct_change() * 100
	df["qqq_ret"] = df["QQQ"].pct_change() * 100
	df["qqq_next"] = df["qqq_ret"].shift(-1) # tomorrow's qqq return
	v_up = df[df["v_ret"] > 0]
	v_down = df[df["v_ret"] < 0]
	print(f"after V up:  QQQ next day avg{v_up['qqq_next'].mean():+.3f}%")
	print(f"after V down:  QQQ next day avg{v_down['qqq_next'].mean():+.3f}%")

def report(df, label):
	fade = df["fade"].sum()
	vsum = df["v_ret"].sum()
	qqqsum = df["qqq_ret"].sum()

	print(f"\n=== {label} ===")
	print(f"fade = {fade:.2f}, qqq sum: {qqqsum:.2f}, v sum: {vsum:.2f} ")

def main():
	df = build(3)
	df = test_leadlag(df)
	

if __name__ == '__main__':
	main()