import pandas as pd
import yfinance as yf

tickers = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","BRK-B","LLY","AVGO","TSLA",
    "JPM","V","UNH","XOM","MA","IONQ","ASTS","GLW","CAT","ORCL",
    "ASPI","TSM","LEU","MRK","LULU","MDB","ARM","WMT","CRM","MCD",
    "TER","CSCO","SKHY","MRNA","BNTX","DHR","WFC","TXN","VZ","AMD",
    "PM","DIS","INTC","NXE","NFLX","CAT","UNP","IBM","GE","QCOM",
    "NEE","HON","AMGN","LUNR","RKLB","BA","NKE","NIO","GS","ADI",
    "CRWV","NET","PLTR","PANW","BLK","SNOW","DELL","SPCX","DE","GILD",
]

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

def ma_signal(closes, window = 50):
	ma = closes.rolling(window).mean()
	signal = (closes > ma).astype(int)
	return signal


def strategy_returns(closes, signal):
	rets = closes.pct_change()
	lagged = signal.shift(1)
	strat = lagged * rets
	return strat.dropna()

def compare(closes, ticker):
	sig = ma_signal(closes)
	strat = strategy_returns(closes,sig)
	hold_rets = closes.pct_change().dropna()
	strat_total =  (1 + strat).prod() - 1
	hold_total =  (1 + hold_rets).prod() - 1
	print(f"{ticker:6} strat {strat_total*100:.2f}% hold total: {hold_total*100:.1f}%")
	return strat_total, hold_total

def main():
	wins = 0
	total = 0
	for tk in tickers:
		closes = get_closes(tk,3)
		if closes is None:
			continue
		comparetk = compare(closes, tk)
		strat_total, hold_total = comparetk
		if strat_total > hold_total:
			wins += 1
		total +=1
	print(f"\nMA-cross beat buy-and-hold in {wins}/{total} names")

if __name__ == '__main__':
	main()
