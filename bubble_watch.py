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
    rows.sort(key=lambda r: RANK[r[2]])
    return rows

def all_values():
    v = get_auto()
    for metric, data in load_manual().items():
        v[metric] = data["value"]
    return v
	
print(evaluate(all_values(), load_manual()))