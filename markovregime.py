def label_state(ret, band):
	"""Given one day's return, return a string label: "up", "down", or "flat". The band is a small threshold (say 0.25%) so tiny moves count as "flat" rather than noise-labeled up/down.
"""
	if ret > band:
		return "up"
	elif -ret < band:
		return "down"
	else:
		return "flat"

def count_transisitions(labels):
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

	labels = np.array ([label_state(r, band) for r in frame["ret"]])
	counts = count_transitions(labels)
	trans = normalize_rows(counts)
	base = base_rates(labels)

	return counts, trans, base


