import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

EVENTS = [
    # date       actual  consensus
    ("2025-06-13", 0.6, 0.6),
    ("2025-06-21", 0.5, 0.6),
    ("2026-02-28", -0.3, -0.3),
    ("2026-03-06", 0.2, 0.1),
    ("2026-03-21", 0.1, 0.1),
    ("2026-05-25", -0.1, -0.2),
    ("2026-06-11", 0.2, 0.1),
]

tickers = ["SPY", "QQQ", "SOXX"]


def surprise(actual, consenses):
	 return actual - consenses
	
def bucket(surprise):
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
	data = yf.download(ticker, start=start,
		end=end, progress=False)
	if data.empty:
		return None
	if isinstance(data.columns, pd.MultiIndex):      # flatten multi-level cols
		data.columns = data.columns.get_level_values(0)
	closes = data["Close"]
	idx = closes.index

	# find the first trading day after the release day
	later = idx[idx >= pd.Timestamp(event_date)]
	if len(later) == 0:
		return None
	pos = idx.get_loc(later[0]) # positions of release day

	# close days 
	target = pos + days
	if target >= len(closes):
		return None

	# percent change
	close_release = closes.iloc[pos]
	close_later = closes.iloc[target]

	return (close_later /  close_release - 1) * 100

def main():
	for date, actual, consenses in EVENTS:
		reading = surprise(actual, consenses)
		expectation = bucket(reading)
		print(f"\n{date}: surprise {reading:+.2f}pp ({expectation})")

		for tk in tickers:
			r = reaction(tk, date, 7)
			if r is None:
				priint (f" {tk}: No data")
			else:
				print(f" {tk}: {r:+.2f}% over 7 days")


if __name__ == '__main__':
	main()


