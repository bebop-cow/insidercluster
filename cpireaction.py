import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

def surprise(actual, consenses):
	 return actual - consenses
	
def bucker(surprise):
	if surprise > 0:
		return "hotter"
	elif surprise < 0:
		return "cooler"
	else:
		return "inline"

def reaction(ticker, event_date, days=7):
	# download a window that safely brackets event_date + N trading days
    start = pd.Timestamp(event_date) - pd.Timedelta(days=5)
    end   = pd.Timestamp(event_date) + pd.Timedelta(days=days + 10)
	data = yf.download(tickers, start=start,
                       end=end, progress=False)
	if data.empty:
        return None
    closes = data["Close"]
    idx = closes.index

    # find the first trading day after the release day
	later = idx[idx >= pd.Timestamp(start)]
	if len(later) == 0:
		return None
	pos = idx.get_loc(later[0]) # positions of release day

	# close days 
	target = pos + days
	if target >= len(closes):
		return None

	# percent change
	close_release = close.iloc[pos]
	close_later = closes.iloc[later]

	
    return percent_change = ((close_later /  close_release - 1) * 100)