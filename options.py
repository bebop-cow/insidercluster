import yfinance as yfinance
tk = yf.Ticker(ticker)

for expiry in tk.options:
	chain = tk.option_chain(expiry)
	calls = chain.calls
	puts = chain.puts
	cnear = calls[abs(calls["lastPrice"] - target) <= 25]
	pnear = puts[abs(puts["lastPrice"] - target) <= 25]