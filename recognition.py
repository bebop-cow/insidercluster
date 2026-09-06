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

def gap_trend(ticker):
    tk  = yf.Ticker(ticker)
    try:
        capex = tk.quarterly_cashflow.loc["Capital Expenditure"].abs()
        dep = tk.quarterly_cashflow,loc["Depreciation and Amortization"]
        ratio = capex / dep
        return ratio
    except Exception:
        return None

def main():
    print(gap_trend("GOOGL"))

if __name__ == '__main__':
    main()