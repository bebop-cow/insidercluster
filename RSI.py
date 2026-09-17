import pandas as pd
import yfinance as yf
import sys

def rsi(closes, window=14):
	delta = closes.diff()
	gains = delta.clip(lower=0)
	loses = -delta.clip(upper=0)
	avg_gain = gains.rolling(window).mean()