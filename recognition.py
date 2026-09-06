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

rev,capex,dep = get_fundamentals("META")
print(f"{rev:.1f}, {capex:.1f}, {dep:.1f}")