import pandas as pd
from twos10s30s import fetch_series   # or wherever fetch_series lives
import requests
import os
from dotenv import load_dotenv
here = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(here, ".env"))
NTFY_KEY = os.getenv("NTFY_KEY")

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
BINARY_METRICS = {"capex_revision"}
RISING_METRICS = {"nvda_ar_concentration"}
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

def flag_rising(value, prev, red_rise=10.0, amber_rise=3.0):
    rise = value - prev
    if rise >= red_rise:
        return "RED"
    elif rise >= amber_rise:
        return "AMBER"
    else:
        return "GREEN"

def flag_binary(value):
    return "RED" if value >= 1 else "GREEN"

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
        elif metric in BINARY_METRICS:
        	flag = flag_binary(val)
        elif metric in RISING_METRICS:
        	prev = manual[metric]["prev"]
        	flag = flag_rising(val, prev)
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
    names = [r["ticker"] for r in hits]
    return n, flag, names

def flag_custody():
    s = fetch_series("WMTSECL1").dropna()
    now = s.iloc[-1]
    prev = s.iloc[-5]                    # ~4 weeks ago
    flag = flag_decel(now, prev, red_drop=40000, amber_drop=15000)   # in millions
    return now, flag

def credit_watch():
    df = pd.read_csv("credit_watch.csv", parse_dates=["date"])
    df = df.sort_values("date")
    groups = df.groupby(["ticker", "bond_type"]).tail(2)
    return groups

def latest_pairs():
    df = credit_watch()                        # the last-2-rows frame
    out = []
    for (ticker, btype), g in df.groupby(["ticker","bond_type"]):
        g = g.sort_values("date")
        latest = g.iloc[-1]
        prev = g.iloc[-2]["yield"] if len(g) >= 2 else None
        out.append({
            "ticker": ticker, "bond_type": btype,
            "yield": latest["yield"], "prev": prev,
            "cusip": latest["cusip"],
        })
    return out

def flag_spread(bond_yield, y30):
    spread = bond_yield - y30
    return flag_level(spread, red=5.0, amber=2.0, higher_is_worse=True)

def flag_wow(bond_yield, prev):
    if prev is None:
        return "GREEN"                    # no history yet
    rise = bond_yield - prev
    return "RED" if rise >= 0.5 else "GREEN"    # 0.5 points = 50bp

def credit_rows(y30):
    rows = []
    for bond in latest_pairs():
        spread_flag = flag_spread(bond["yield"], y30)
        wow_flag    = flag_wow(bond["yield"], bond["prev"])
        # take the worse of the two
        flag = spread_flag if RANK[spread_flag] <= RANK[wow_flag] else wow_flag
        label = f"{bond['ticker']}_{bond['bond_type']}"
        rows.append((label, bond["yield"], flag))
    return rows

def flag_syndication():
    df = pd.read_csv("syndication_watch.csv", parse_dates=["date_reported"])
    cutoff = pd.Timestamp.now() - pd.DateOffset(days=90)
    recent = df[df["date_reported"] >= cutoff]
    stalled = recent[(recent["days_stuck"] >60) | (recent["status"].isin(["stalled", "discount", "pulled"]))]
    n = len(stalled)
    flag = "RED" if n >= 2 else "AMBER" if n >= 1 else "GREEN"
    return n, flag

def ai_credit_basket(y30):
    bonds = latest_pairs()
    spreads = [b["yield"] - y30 for b in bonds if b["bond_type"] == "unsecured"]
    if not spreads:
        return None
    avg = sum(spreads) / len(spreads)
    flag = flag_level(avg, red=5.0, amber=2.0, higher_is_worse=True)
    return avg, flag

import json

def save_flags(rows, path="bubble_state.json"):
    state = {metric: flag for metric, value, flag in rows}
    with open(path, "w") as f:
        json.dump(state, f)

def load_flags(path="bubble_state.json"):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}        # first run — no prior state

def find_flips(old, new):
    flips = []
    for metric, new_flag in new.items():
        old_flag = old.get(metric)              # None if metric is new
        if old_flag != new_flag:
            flips.append((metric, old_flag, new_flag))
    return flips

def notify_flips(flips):
    lines = [f"{m}: {old}→{new}" for m, old, new in flips]
    body = "\n".join(lines)
    requests.post(
        f"https://ntfy.sh/{NTFY_KEY}",
        data=body.encode("utf-8"),
        headers={"Title": "Bubble Watch - flips"},
    )

def secured_gap(ticker):
    bonds = latest_pairs()
    sec = next((b["yield"] for b in bonds if b["ticker"]==ticker and b["bond_type"]=="secured"), None)
    uns = next((b["yield"] for b in bonds if b["ticker"]==ticker and b["bond_type"]=="unsecured"), None)
    if sec is None or uns is None:
        return None                         # need both to compute a gap
    gap = uns - sec
    flag = flag_level(gap, red=8.0, amber=4.0, higher_is_worse=True)
    return gap, flag

def main():
    rows = evaluate(all_values(), load_manual())
    n, flag, names = flag_clusters()
    rows.append(("insider_clusters", n, flag))
    if names:
        print(f" insider cluster: {', '.join(names)}")
    now, flag = flag_custody()
    rows.append(("foreign_custody", round(now/1000, 0), flag))   # /1000 to show in billions
    y30 = get_auto()["30Y"]
    rows.extend(credit_rows(y30))        # extend, not append — it's a list of rows
    n, flag = flag_syndication()
    rows.append(("syndication", n, flag))
    avg, flag = ai_credit_basket(y30)
    rows.append(("ai credit", round(avg, 2), flag))
    rows.sort(key=lambda r: RANK[r[2]])      # re-sort with the new row
    show(rows)

    old = load_flags()
    new = {metric: flag for metric, value, flag in rows}
    flips = find_flips(old, new)
    if flips:
        notify_flips(flips)
    save_flags(rows)

    for tk in set(b["ticker"] for b in latest_pairs()):
        result = secured_gap(tk)
        if result:
            gap, flag = result
            rows.append((f"{tk}_sec_gap", round(gap, 2), flag))
    
    

if __name__ == '__main__':
    main()