import yfinance as yf
tk = yf.Ticker(ticker)

for expiry in tk.options:
	chain = tk.option_chain(expiry)
	calls = chain.calls
	puts = chain.puts
	calls["mid"] = (calls["bid"] + calls["ask"]) / 2
	cnear = calls[abs(calls["mid"] - target) <= 25]
	puts["mid"] = (puts["bid"] + puts["ask"]) / 2
	pnear = puts[abs(puts["mid"] - target) <= 25]