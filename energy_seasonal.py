import yfinance as yf
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def monthly_returns(ticker, years=6):
    closes = yf.Ticker(ticker).history(period=f"{years}y")["Close"].dropna()
    if closes.empty:
        return None
    month_end = closes.resample("ME").last()
    returns = month_end.pct_change() * 100
    return returns.dropna()

print(monthly_returns("XLE").tail(12))