import mathplotlib.pyplot as plt
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
        dep = tk.quarterly_cashflow.loc["Depreciation and Amortization"]
        ratio = capex / dep
        return ratio
    except Exception:
        return None
   
    return ratio.dropna()

def plot_trends(tickers):
    for tk in tickers:
        trend = gap_trend(tk)
        if trend is None:
            continue
        s = trend[::-1]
        plt.plot(s.index, s.values, marker = "o", label=tk)
    plt.legend()
    plt.ylabel("capex / depreciation")
    plt.table("AI capex deferral trend")


def main():
    want_chart = "--chart" in sys.argv
    for tk in ["META", "MSFT", "AMZN", "NVDA"]:
        print(f"\n{tk}:")
        print(gap_trend(tk))

    if want_chart:
        plot_trends(tickers)


if __name__ == '__main__':
    main()