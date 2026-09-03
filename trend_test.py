def ma_signal(closes, window = 50):
	ma = closes.rolling(window).mean()
	signal = (closes > ma).astype(int)
	return signal