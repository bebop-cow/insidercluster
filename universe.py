import pandas as pd
import yfinance as yf

def build_universe(tickers, years=10):
    end = pd.Timestamp.now()
    start = end - pd.DateOffset(years=years)
    data = yf.download(tickers, start=start.strftime("%Y-%m-%d"),
                       end=end.strftime("%Y-%m-%d"), progress=False)
    closes = data["Close"]          # just the Close block
    return closes.dropna()

def monthly_returns(closes):
    # 1. downsample daily closes to month-end (last close each month)
    monthly = closes.resample("ME").last()
    # 2. percent change month-over-month
    rets = monthly.pct_change()
    # 3. drop the first row (NaN from pct_change)
    return rets.dropna()

def momentum_score(rets, lookback=12, skip=1):
    # cumulative return over the window [t-lookback, t-skip]
    # rets are simple monthly returns; compounding = (1+r) product minus 1
    cum = (1 + rets).rolling(lookback - skip).apply(lambda x: x.prod()) - 1
    # shift by `skip` so the most recent `skip` months are excluded
    return cum.shift(skip)

def rank_scores(scores):
    return scores.rank(axis=1, ascending=False)   # 1 = strongest

def select_portfolio(ranks, top_n):
    # 1. boolean table: True where rank is in the top N
    held = ranks <= top_n
    # 2. convert True/False to equal weights that sum to 1 per row
    weights = held.div(held.sum(axis=1), axis=0)
    return weights

def strategy_returns(weights, rets):
    # 1. align: this month's weights earn NEXT month's returns
    #    shift returns back so row t holds t+1's return
    fwd = rets.shift(-1)
    # 2. weighted return per ticker, then sum across tickers per month
    port = (weights * fwd).sum(axis=1)
    return port.dropna()

def main():
    tickers = ["TSLA","ARM","LLY","AAPL","GOOGL","NVDA","ORCL","META","V","GS","LEU","NKE"]

    closes = build_universe(tickers ,years=10)
    rets = monthly_returns(closes)
    scores = momentum_score(rets, lookback=12, skip=1)
    ranks = rank_scores(scores)
    weights = select_portfolio(ranks,5)
    port = strategy_returns(weights, rets)

    strat = (1 + port).prod() - 1
    hold = (1 + rets.mean(axis=1)).prod() - 1

    print("momentum:   ", round(strat, 3))
    print("buy & hold: ", round(hold, 3))



        

if __name__ == "__main__":
    main()
