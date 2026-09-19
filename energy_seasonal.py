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



def seasonal(ticker, years=6):
    rets = monthly_returns(ticker,years)
    groups = rets.groupby(rets.index.month).mean()
    counts = rets.groupby(rets.index.month).count()
    return groups, counts


groups, counts = seasonal("XLE")
for month in range(1, 13):
    print(f"month {month:2d}: {groups[month]:+.2f}%  (n={counts[month]})")