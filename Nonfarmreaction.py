import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)

EVENTS = [
    ("2026-08-07", -23, 80),    # -103K cool
    ("2026-07-02", 57, 110),    #  -53K cool
    ("2026-06-05", 172, 85),    #  +87K HOT
    ("2026-05-08", 115, 62),    #  +53K HOT
    ("2026-04-03", 178, 60),    # +118K HOT
    ("2026-03-06", -92, 59),    # -151K cool
    ("2026-02-11", 130, 70),    #  +60K HOT
    ("2026-01-09", 50, 60),     #  -10K inline
    ("2025-12-16", 64, 50),     #  +14K inline
    ("2025-11-20", 119, 50),    #  +69K HOT
    ("2025-09-05", 22, 75),     #  -53K cool
    ("2025-08-01", 73, 110),    #  -37K cool
    ("2025-07-03", 147, 110),   #  +37K HOT
    ("2025-06-06", 139, 130),   #   +9K inline
    ("2025-05-02", 177, 130),   #  +47K HOT
    ("2025-04-04", 228, 135),   #  +93K HOT
    ("2025-03-07", 151, 160),   #   -9K inline
    ("2025-02-07", 143, 170),   #  -27K cool
    ("2025-01-10", 256, 160),   #  +96K HOT
    ("2024-12-06", 227, 200),   #  +27K HOT
    ("2024-11-01", 12, 113),    # -101K cool
    ("2024-10-04", 254, 140),   # +114K HOT
    ("2024-09-06", 142, 160),   #  -18K inline
    ("2024-08-02", 114, 175),   #  -61K cool
    ("2024-07-05", 206, 190),   #  +16K inline
    ("2024-06-07", 272, 185),   #  +87K HOT
    ("2024-05-03", 175, 243),   #  -68K cool
    ("2024-04-05", 303, 200),   # +103K HOT
    ("2024-03-08", 275, 200),   #  +75K HOT
    ("2024-02-02", 353, 180),   # +173K HOT
    ("2024-01-05", 216, 170),   #  +46K HOT
    ("2023-12-08", 199, 180),   #  +19K inline
    ("2023-11-03", 150, 180),   #  -30K cool
    ("2023-10-06", 336, 170),   # +166K HOT
    ("2023-09-01", 187, 170),   #  +17K inline
    ("2023-08-04", 187, 200),   #  -13K inline
    ("2023-07-07", 209, 225),   #  -16K inline
    ("2023-06-02", 339, 190),   # +149K HOT
    ("2023-05-05", 253, 180),   #  +73K HOT
    ("2023-04-07", 236, 239),   #   -3K inline
    ("2023-03-10", 311, 205),   # +106K HOT
    ("2023-02-03", 517, 185),   # +332K HOT
    ("2023-01-06", 223, 200),   #  +23K inline
    ("2022-12-02", 263, 200),   #  +63K HOT
    ("2022-11-04", 261, 200),   #  +61K HOT
    ("2022-10-07", 263, 250),   #  +13K inline
    ("2022-09-02", 315, 300),   #  +15K inline
    ("2022-08-05", 528, 250),   # +278K HOT
    ("2022-07-08", 372, 268),   # +104K HOT
    ("2022-06-03", 390, 325),   #  +65K HOT
    ("2022-05-06", 428, 391),   #  +37K HOT
    ("2022-04-01", 431, 490),   #  -59K cool
    ("2022-03-04", 678, 400),   # +278K HOT
    ("2022-02-04", 467, 150),   # +317K HOT
    ("2022-01-07", 199, 400),   # -201K cool
]

tickers = ["SPY", "QQQ", "SOXX"]


def surprise(actual, consenses):
	 return actual - consenses
	
def bucket(surprise, band=25):
	if surprise > band:
		return "hotter"
	elif surprise < -band:
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

	buckets = {"hotter": {"SPY": [], "QQQ": [], "SOXX": []},
				"cooler": {"SPY": [], "QQQ": [], "SOXX": []},
				"inline": {"SPY": [], "QQQ": [], "SOXX": []}}

	for date, actual, consenses in EVENTS:
		reading = surprise(actual, consenses)
		expectation = bucket(reading)
		# print(f"\n{date}: surprise {reading:+.2f}pp ({expectation})")

		for tk in tickers:
			r = reaction(tk, date, 1)
			if r is not None:
				buckets[expectation][tk].append(r)
			# if r is None:
			# 	print (f" {tk}: No data")
			# else:
			# 	print(f" {tk}: {r:+.2f}% over 7 days")

	for buck in ["hotter", "cooler", "inline"]:
		for tk in ["SPY", "QQQ", "SOXX"]:
			vals = buckets[buck][tk]
            # average if non-empty, print buck, tk, mean, count
			if not vals:
				continue
			combined = sum(vals)/len(vals)
			count = len(vals)
			print(f"{buck:7} {tk:5} avg {combined:+.2f}%  (n={count})")


if __name__ == '__main__':
	main()


