import yfinance as yf
for sym in ["^TNX", "JGB=F", "^JP10Y", "JP10Y=RR"]:
    try:
        h = yf.Ticker(sym).history(period="5d")["Close"]
        print(sym, "->", len(h), "rows", h.iloc[-1] if len(h) else "empty")
    except Exception as e:
        print(sym, "FAILED", e)