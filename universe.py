import pandas as pd
import yfinance as yf

split = "2021-01-01"

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

def signal_reversal(rets, lookback=1):
    # recent return over `lookback` months, then flip the sign
    recent = (1 + rets).rolling(lookback).apply(lambda x: x.prod()) - 1
    return -recent          # flip so losers rank highest

def signal_lowvol(rets, lookback=6):
    # trailing volatility = rolling std of returns over `lookback` months
    vol = rets.rolling(lookback).std()
    return -vol          # flip so lowest-vol ranks highest

def score_signal(scores, rets, split_date, top_n=5):
    # 1. keep only test-period rows (index >= split_date)
    test_scores = scores[scores.index >= split_date]
    test_rets   = rets[rets.index >= split_date]
    # 2. rank → select → returns (reuse your functions)
    ranks   = rank_scores(test_scores)
    weights = select_portfolio(ranks,top_n)
    port    = strategy_returns(weights,test_rets)
    # 3. strategy total return vs buy & hold, both on the test window
    strat = (1 + port).prod() - 1
    hold  = (1 + test_rets.mean(axis=1)).prod() - 1
    return strat, hold

def combine_signals(signal_list):
    # each signal: z-score it per month (row), so all are same scale
    z = [s.sub(s.mean(axis=1), axis=0).div(s.std(axis=1), axis=0)
         for s in signal_list]
    # average the z-scored tables element-wise
    combined = sum(z)/len(z)
    return combined

def main():
    tickers = ["TSLA","ARM","LLY","AAPL","GOOGL","NVDA","ORCL","META","V","GS","LEU","NKE"]
    closes = build_universe(tickers)
    rets = monthly_returns(closes)

    # score each weak signal SOLO on the test window (survival check)
    m_strat, m_hold = score_signal(momentum_score(rets), rets, split)
    print("momentum ", round(m_strat,3), "vs hold", round(m_hold,3))

    r_strat, r_hold = score_signal(signal_reversal(rets), rets, split)
    print("reversal ", round(r_strat,3), "vs hold", round(r_hold,3))

    l_strat, l_hold = score_signal(signal_lowvol(rets), rets, split)
    print("lowvol   ", round(l_strat,3), "vs hold", round(l_hold,3))

    # combine all three, score the blend the same way
    combo = combine_signals([momentum_score(rets), signal_reversal(rets), signal_lowvol(rets)])
    c_strat, c_hold = score_signal(combo, rets, split)
    print("COMBINED ", round(c_strat,3), "vs hold", round(c_hold,3))

if __name__ == "__main__":
    main()