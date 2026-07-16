import sys
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: pip install yfinance pandas numpy")
    sys.exit(1)


def label_state(ret, band):
	"""Given one day's return, return a string label: "up", "down", or "flat". The band is a small threshold (say 0.25%) so tiny moves count as "flat" rather than noise-labeled up/down.
"""
	if ret > band:
		return "up"
	elif ret < -band:
		return "down"
	else:
		return "flat"

def count_transitions(labels):
	"""Input: a list of labels like ["up", "flat", "down", "up", ...].
Output: a 3×3 numpy array where counts[i][j] = number of times state i was followed by state j"""
	states = ["down", "flat", "up"]
	idx = {"down": 0, "flat": 1, "up": 2}

	counts = np.zeros((3, 3))
	for today,tomorrow in zip(labels[:-1], labels[1:]) :
		counts[idx[today]][idx[tomorrow]] += 1
	return counts

def normalize_rows(counts):
	"""Turn counts into probabilities - each row sums to 1. trans[i][j] = P(tomorrow = j | today = i)."""

	trans = np.zeros((3, 3))
	for i in range(3):
		rowsum = counts[i].sum()
		if rowsum == 0:
			continue
		else:
			trans[i] = counts[i]/ rowsum
	return trans

def base_rates(labels):
	"""return a length-3 array of how often each state occurs overall"""
	states = ["down", "flat", "up"]
	counts = np.array ([labels.count(s) for s in states])
	return counts/ counts.sum()

def markov_chain(frame, band):
	"""glue the four functions together"""

	labels = [label_state(r, band) for r in frame["ret"]]
	counts = count_transitions(labels)
	trans = normalize_rows(counts)
	base = base_rates(labels)

	return counts, trans, base

def edge_check(trans, base):
    states = ["down", "flat", "up"]
    delta = (trans - base) * 100        # numpy broadcasts base across rows
    df = pd.DataFrame(delta,
                      index=[f"from {s}" for s in states],
                      columns=[f"->{s}" for s in states])
    print("edge (row minus base, pct points):")
    print(df.round(1))

def build_frame(ticker, years=10):
	end = pd.Timestamp.now()
	start = end - pd.DateOffset(years=years)
	df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
		end=end.strftime("%Y-%m-%d"), progress=False)
	if df.empty:
		return None
	df = flatten_columns(df)
	df = df[["Close"]].copy()
	df["ret"] = df["Close"].pct_change() * 100
	df["next_ret"] = df["ret"].shift(-1)
	df = df.dropna()
	df["vol"] = df["ret"].rolling(10).std()
	return df

def print_chain(ticker, trans, base):
    states = ["down", "flat", "up"]
    df = pd.DataFrame(trans,
                      index=[f"from {s}" for s in states],
                      columns=[f"->{s}" for s in states])
    print(ticker)
    print(df.round(3))
    print("base:", np.round(base, 3))

def flatten_columns(df):
	if isinstance(df.columns, pd.MultiIndex):
		df.columns = df.columns.get_level_values(0)
	return df

def main():
    for ticker in ["QQQ", "SOXX"]:
        frame = build_frame(ticker)
        counts, trans, base = markov_chain(frame, 0.25)
       

        print_chain(ticker, trans, base)
        edge_check(trans,base)

if __name__ == "__main__":
    main()
