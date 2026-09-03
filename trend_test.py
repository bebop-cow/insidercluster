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
