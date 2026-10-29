import yfinance as yf
import pandas as pd


def pull_options(ticker, target, window =25):
	tk = yf.Ticker(ticker)
	cutoff = pd.Timestamp.now() + pd.Timedelta(days=21)
	all_calls =[]
	all_puts = []
	for expiry in tk.options:
		if pd.Timestamp(expiry) > cutoff:
			break
		chain = tk.option_chain(expiry)
		calls = chain.calls
		puts = chain.puts
		calls["mid"] = (calls["bid"] + calls["ask"]) / 2
		cnear = calls[abs(calls["mid"] - target) <= window].copy()
		cnear["expiry"] = expiry
		all_calls.append(cnear)
		puts["mid"] = (puts["bid"] + puts["ask"]) / 2
		pnear = puts[abs(puts["mid"] - target) <= window].copy()
		pnear["expiry"] = expiry
		all_puts.append(pnear)

	calls_df = pd.concat(all_calls) if all_calls else pd.DataFrame()
	puts_df = pd.concat(all_puts) if all_puts else pd.DataFrame()

	return calls_df, puts_df