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

THRESHOLDS = {
    "10Y":        {"red": 5.0,  "amber": 4.75, "higher_worse": True},
    "30Y":        {"red": 5.5,  "amber": 5.25, "higher_worse": True},
    "CCC_OAS":  {"red": 15.0, "amber": 13.5, "higher_worse": True},
    "HY_OAS":   {"red": 5.5,  "amber": 4.5,  "higher_worse": True},
    "RPO_growth": {"red": 0.0,  "amber": 5.0,  "higher_worse": False},
    "cloud_growth":{"red": 10.0, "amber": 15.0, "higher_worse": False},
}

from twos10s30s import fetch_series   # or wherever fetch_series lives

ccc = fetch_series("BAMLH0A3HYC")
hy = fetch_series("BAMLH0A0HYM2")
print(f"CCC OAS: {ccc.iloc[-1]:.2f}%")
print(f"HY OAS:  {hy.iloc[-1]:.2f}%")