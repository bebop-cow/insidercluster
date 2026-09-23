import os
from dotenv import load_dotenv
import requests
import yfinance as yf
import pandas as pd

load_dotenv()
KEY = os.getenv("EIA_KEY")

# ══════════════════════════════════════════════════════════════════
# DATA FETCHERS
# ══════════════════════════════════════════════════════════════════

def get_eia_series(series_id, route, n=8):
    """Weekly US petroleum series (inventories, production, SPR, refinery)."""
    url = f"https://api.eia.gov/v2/petroleum/{route}/data/"
    params = {
        "api_key": KEY, "frequency": "weekly", "data[0]": "value",
        "facets[series][]": series_id,
        "sort[0][column]": "period", "sort[0][direction]": "desc",
        "length": n,
    }
    rows = requests.get(url, params=params, timeout=20).json()["response"]["data"]
    return [(row["period"], float(row["value"])) for row in rows]


def intl_production(country, n=6):
    """Monthly crude production by country (EIA International). Lags ~4-6mo."""
    url = "https://api.eia.gov/v2/international/data/"
    params = {
        "api_key": KEY, "frequency": "monthly", "data[0]": "value",
        "facets[productId][]": "57",       # crude incl. lease condensate
        "facets[activityId][]": "1",       # production
        "facets[countryRegionId][]": country,
        "sort[0][column]": "period", "sort[0][direction]": "desc",
        "length": n,
    }
    rows = requests.get(url, params=params, timeout=20).json()["response"]["data"]
    return [(row["period"], float(row["value"])) for row in rows]


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def rel_strength(ticker, months=3):
    """Ticker's return minus SPY's over the window. Positive = outperforming."""
    end = pd.Timestamp.now()
    start = end - pd.DateOffset(months=months)
    df = yf.download([ticker, "SPY"], start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)
    closes = df["Close"].dropna()
    tk_ret = (closes[ticker].iloc[-1] / closes[ticker].iloc[0] - 1) * 100
    spy_ret = (closes["SPY"].iloc[-1] / closes["SPY"].iloc[0] - 1) * 100
    return tk_ret - spy_ret


# ══════════════════════════════════════════════════════════════════
# SECTOR SCANS  (return rows; the Streamlit page displays them)
# ══════════════════════════════════════════════════════════════════

def _scan(basket):
    """Shared: score a {group: [tickers]} basket on RS + 50d trend."""
    rows = []
    for group, tickers in basket.items():
        for tk in tickers:
            try:
                rs = rel_strength(tk)
                closes = yf.Ticker(tk).history(period="6mo")["Close"].dropna()
                up = closes.iloc[-1] > closes.rolling(50).mean().iloc[-1]
                rows.append((group, tk, round(rs, 1), "up" if up else "down"))
            except Exception:
                rows.append((group, tk, None, "no data"))
    return rows


def nuclear_scan():
    return _scan({
        "Miner": ["CCJ"], "Enrich": ["LEU"],
        "SMR": ["OKLO", "NNE", "SMR"],
        "AI-Utility": ["CEG", "VST", "TLN"],
        "Uranium": ["URA", "SRUUF"],
    })


def solar_breakdown():
    return _scan({
        "Solar-ETF": ["TAN"],
        "Residential": ["RUN", "ENPH", "SEDG"],
        "Utility-scale": ["FSLR"],
        "Comparators": ["ICLN", "ARKK", "TLT"],
    })


def scorecard():
    """Oil/Solar/Nuclear top-level: RS + multi-timeframe trend."""
    sectors = {"Oil": "XLE", "Solar": "TAN", "Nuclear": "URA"}
    out = []
    for name, tk in sectors.items():
        rs = rel_strength(tk)
        closes = yf.Ticker(tk).history(period="5y")["Close"].dropna()
        last = closes.iloc[-1]
        out.append({
            "sector": name, "ticker": tk, "rs": round(rs, 1),
            "ma50": last > closes.rolling(50).mean().iloc[-1],
            "yoy": last > closes.rolling(252).mean().iloc[-1],
            "y5": last > closes.rolling(1250).mean().iloc[-1],
        })
    return out


# ══════════════════════════════════════════════════════════════════
# GULF / MIDDLE EAST OUTPUT
# ══════════════════════════════════════════════════════════════════

def gulf_output():
    """Sum of Gulf crude production + per-country 3mo change.
    NOTE: reflects real 2026 Iran-war supply disruption from Mar 2026 on
    (verified: ~10M bpd Gulf output lost by mid-March per IEA/EIA)."""
    gulf = {"Saudi": "SAU", "UAE": "ARE", "Kuwait": "KWT",
            "Iraq": "IRQ", "Iran": "IRN", "Qatar": "QAT"}
    total = 0.0
    breakdown = []
    for name, code in gulf.items():
        data = intl_production(code)
        latest = data[0][1]
        prev = data[3][1]          # ~3 months earlier
        total += latest
        breakdown.append((name, latest, latest - prev))
    return total, breakdown




def main():
    print("=== OIL FUNDAMENTALS (weekly, 4wk change) ===")
    for label, sid, route, unit in [
        ("Inventories", "WCESTUS1", "stoc/wstk", "k"),
        ("Production", "WCRFPUS2", "sum/sndw", "k/d"),
        ("SPR", "WCSSTUS1", "sum/sndw", "k"),
        ("Gasoline demand", "WGFUPUS2", "sum/sndw", "k/d"),
    ]:
        d = get_eia_series(sid, route)
        chg = d[0][1] - d[4][1]
        print(f"  {label:16} {chg:+,.0f}{unit}")

    print("\n=== GULF OUTPUT (monthly, war-disrupted) ===")
    total, breakdown = gulf_output()
    print(f"  Total: {total:,.0f} TBPD")
    for name, latest, chg in breakdown:
        print(f"    {name:8} {latest:,.0f} ({chg:+,.0f} 3mo)")


if __name__ == "__main__":
    main()