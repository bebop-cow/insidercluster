import yfinance as yf

def probe_yf(ticker):
    tk = yf.Ticker(ticker)
    print("=== CASHFLOW (quarterly) ===")
    cf = tk.quarterly_cashflow
    print(cf.index.tolist())          # the row labels available
    print("\n=== INCOME (quarterly) ===")
    inc = tk.quarterly_financials
    print(inc.index.tolist())

def get_fundamentals(ticker):
    tk = yf.Ticker(ticker)
    try:
        rev = tk.quarterly_financials.loc["Total Revenue"].iloc[0]
        capex = abs(tk.quarterly_cashflow.loc["Capital Expenditure"].iloc[0])
        dep = tk.quarterly_cashflow.loc["Depreciation And Amortization"].iloc[0]
        return rev, capex, dep
    except Exception:
        return None

def capex_depreciation_gap(tickers):
    results = []
    for tk in tickers:
        r = get_fundamentals(tk)
        if r is None:
            continue                 # skip bad ticker, keep going

        rev, capex, dep = r
        gap = capex - dep
        ratio = capex / dep
        
        results.append((tk, capex, dep, gap, ratio))
    return results

def main():
    tickers = ["META", "MSFT", "GOOGL", "AMZN"]
    gaps = capex_depreciation_gap(tickers)
    print(f"{'ticker':7}{'capex':>14}{'deprec':>14}{'gap':>14}{'ratio':>7}")
    for tk, capex, dep, gap, ratio in gaps:
        print(f"{tk:7}{capex/1e9:>12.1f}B{dep/1e9:>12.1f}B{gap/1e9:>12.1f}B{ratio:>7.1f}")

if __name__ == '__main__':
    main()