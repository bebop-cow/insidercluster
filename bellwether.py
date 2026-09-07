import yfinance as yf
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def get_closes(ticker, months=18):
    end = pd.Timestamp.now()
    start = end - pd.DateOffset(months=months)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None
    df = flatten_columns(df)
    return df["Close"].dropna()


def build_basket(tickers, months=18):
    # pull every name's closes into ONE aligned DataFrame (one column per ticker)
    data = {}
    for tk in tickers:
        c = get_closes(tk, months)
        if c is not None:
            data[tk] = c
    return pd.DataFrame(data).dropna()      # dates x tickers, aligned


def spread_trend(basket_tickers, months=18, window=63):
    # window=63 trading days ~ 3-month rolling return
    basket = build_basket(basket_tickers, months)
    spy = get_closes("SPY", months)

    # each name's rolling 3mo return, then average across the basket per day
    basket_roll = basket.pct_change(window) * 100      # DataFrame: rolling ret per name
    basket_avg = basket_roll.mean(axis=1)              # average across names each day

    spy_roll = spy.pct_change(window) * 100            # SPY's rolling 3mo return

    # align the two on shared dates, then the spread
    spread = (basket_avg - spy_roll).dropna()
    return spread


def main():
    basket = ["PG", "PEP", "WMT", "COST", "KO", "CAT", "FDX"]
    spread = spread_trend(basket)

    print("basket - SPY (3mo rolling return spread), recent:")
    print(spread.tail(10))
    print(f"\nlatest:  {spread.iloc[-1]:+.1f}%")
    print(f"3mo ago: {spread.iloc[-63]:+.1f}%" if len(spread) > 63 else "")
    direction = "WIDENING (defensiveness fading / risk-on building)" \
        if spread.iloc[-1] < spread.iloc[-63] else "NARROWING (fear returning)"
    if len(spread) > 63:
        print(f"trend: {direction}")

    if "--chart" in __import__("sys").argv and plt:
        spread.plot()
        plt.axhline(0, color="gray", linestyle="--")
        plt.ylabel("basket - SPY (3mo rolling %)")
        plt.title("Defensive consumer vs SPY")
        plt.show()


if __name__ == "__main__":
    main()