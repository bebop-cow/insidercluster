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
    means = rets.groupby(rets.index.month).mean()
    medians = rets.groupby(rets.index.month).median()
    hit_rate = rets.groupby(rets.index.month).apply(lambda x: (x > 0).mean() * 100)
    counts = rets.groupby(rets.index.month).count()
    return means, medians, hit_rate, counts


groups, counts = seasonal("XLE")
for month in range(1, 13):
    print(f"month {month:2d}: {means[month]:+.2f}%, {medians[month]: +:.2f}%, {hit_rate: +:.2f}%, (n={counts[month]})")