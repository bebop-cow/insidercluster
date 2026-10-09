import pandas as pd
from twos10s30s import fetch_series   # or wherever fetch_series lives

THRESHOLDS = {
    "10Y":        {"red": 5.0,  "amber": 4.75, "higher_worse": True},
    "30Y":        {"red": 5.5,  "amber": 5.25, "higher_worse": True},
    "CCC_OAS":  {"red": 15.0, "amber": 13.5, "higher_worse": True},
    "HY_OAS":   {"red": 5.5,  "amber": 4.5,  "higher_worse": True},
    "RPO_growth": {"red": 0.0,  "amber": 5.0,  "higher_worse": False},
    "cloud_growth":{"red": 10.0, "amber": 15.0, "higher_worse": False},
}

RANK = {"RED": 0, "AMBER": 1, "GREEN": 2}
DECEL_METRICS = {"RPO_growth", "cloud_growth"}

AI_CHAIN = ["NVDA","MSFT","GOOGL","AMZN","META","ORCL","AVGO","MU","GEV","ANET","VRT"]

def flag_decel(value, prev, red_drop=4.0, amber_drop=1.0):
    drop = prev - value
    if drop >= red_drop:
        return "RED"
    elif drop >= amber_drop:
        return "AMBER"
    else:
        return "GREEN"

def flag_level(value, red, amber, higher_is_worse=True):
    if higher_is_worse:
        if value >= red:
            return "RED"
        elif value >= amber:
            return "AMBER"
        else:
            return "GREEN"
    else:                                  # lower is worse (growth metrics)
        if value <= red:
            return "RED"
        elif value <= amber:
            return "AMBER"
        else:
            return "GREEN"

def load_manual(path="bubble_manual.csv"):
    try:
        df = pd.read_csv(path).set_index("metric")
        return df.to_dict("index")
    except Exception:
        return {}

def get_auto():
    return {
        "10Y":     fetch_series("DGS10").dropna().iloc[-1],
        "30Y":     fetch_series("DGS30").dropna().iloc[-1],
        "CCC_OAS": fetch_series("BAMLH0A3HYC").dropna().iloc[-1],
        "HY_OAS":  fetch_series("BAMLH0A0HYM2").dropna().iloc[-1],
    }

def evaluate(values, manual):
    rows = []
    for metric, val in values.items():
        if metric in DECEL_METRICS:
            prev = manual[metric]["prev"]
            flag = flag_decel(val, prev)
        else:
            t = THRESHOLDS[metric]
            flag = flag_level(val, t["red"], t["amber"], t["higher_worse"])
        rows.append((metric, round(val, 2), flag))
    ccc, hy = values["CCC_OAS"], values["HY_OAS"]
    gap = round(ccc - hy, 2)
    rows.append(("CCC-HY_gap", gap, flag_divergence(ccc, hy)))
    rows.sort(key=lambda r: RANK[r[2]])
    return rows

def all_values():
    v = get_auto()
    for metric, data in load_manual().items():
        v[metric] = data["value"]
    return v

def flag_divergence(ccc, hy, red=11.0, amber=10.0):
    gap = ccc - hy
    return flag_level(gap, red, amber, higher_is_worse=True)

MARK = {"RED": "🔴", "AMBER": "🟡", "GREEN": "🟢"}

def show(rows):
    print(f"\n{'METRIC':14}{'VALUE':>8}  FLAG")
    print("-" * 34)
    for metric, value, flag in rows:
        print(f"{metric:14}{value:>8}  {MARK[flag]} {flag}")

from insidercluster_v6 import fetch_recent_form4, analyze

def flag_clusters():
    _, sell_rows = analyze(fetch_recent_form4())
    hits = [r for r in sell_rows if r["ticker"] in AI_CHAIN]
    n = len(hits)
    flag = "RED" if n >= 3 else "AMBER" if n >= 1 else "GREEN"
    return n, flag

def main():
    rows = evaluate(all_values(), load_manual())
    n, flag = flag_clusters()
    rows.append(("insider_clusters", n, flag))
    rows.sort(key=lambda r: RANK[r[2]])      # re-sort with the new row
    show(rows)

if __name__ == '__main__':
 	main()