import pandas as pd
import yfinance as yf

tickers = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","BRK-B","LLY","AVGO","TSLA",
    "JPM","V","UNH","XOM","MA","JNJ","PG","HD","COST","ORCL",
    "ABBV","BAC","KO","MRK","CVX","PEP","ADBE","WMT","CRM","MCD",
    "TMO","CSCO","ACN","ABT","LIN","DHR","WFC","TXN","VZ","AMD",
    "PM","DIS","INTC","INTU","COP","CAT","UNP","IBM","GE","QCOM",
    "NEE","HON","AMGN","LOW","SPGI","BA","NKE","RTX","GS","ISRG",
    "PLD","SBUX","BKNG","MDT","BLK","ELV","AXP","T","DE","GILD",
    "LMT","ADP","MDLZ","CVS","VRTX","C","MMC","REGN","SO","PGR",
    "TJX","MO","BSX","ZTS","CB","DUK","SLB","EOG","BMY","NOW",
    "APD","CL","ITW","WM","MU","FCX","EMR","GD","MCK","PYPL",
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

def measure(closes, anchor):
	base = closes[(closes.index >= anchor - pd.DateOffset(months=6)) & (closes.index < anchor)]
	fwd = closes[(closes.index >= anchor) & (closes.index < anchor + pd.DateOffset(months=6))]
	if len(base) < 60 or len(fwd) < 60:
		return None
	base_vol = base.pct_change().std() * (252**0.5) * 100
	base_tightness = (base.max() - base.min()) / base.mean()*100
	forward_return = (fwd.iloc[-1] / fwd.iloc[0] - 1) * 100
	return base_vol, base_tightness, forward_return

def run_study(tickers,anchor, threshold=50):
	rockets = []
	duds = []
	for tk in tickers:
		closes = get_closes(tk, 3)
		if closes is None:
			continue
		result = measure(closes, anchor)
		if result is None:
			continue
		base_vol, base_tightness, forward_return = result
		if forward_return >= threshold:
			rockets.append((tk, base_vol,base_tightness, forward_return))
		else:
			duds.append((tk, base_vol,base_tightness, forward_return))
	return rockets, duds

def main():
    anchor = pd.Timestamp.now() - pd.DateOffset(months=12)
    rockets, duds = run_study(tickers, anchor)

    def avg(group, i):
        vals = [row[i] for row in group]
        return sum(vals)/len(vals) if vals else 0

    print(f"ROCKETS (n={len(rockets)}): base_vol {avg(rockets,1):.1f}%  base_tight {avg(rockets,2):.1f}%")
    print(f"DUDS    (n={len(duds)}): base_vol {avg(duds,1):.1f}%  base_tight {avg(duds,2):.1f}%")

if __name__ == '__main__':
	main()