import os
from dotenv import load_dotenv
import requests

load_dotenv()

KEY = os.getenv("EIA_KEY")

def get_eia_series(series_id, n=80):
	url = "https://api.eia.gov/v2/petroleum/pnp/wiup/data/"
    params = {
        "api_key": KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": series_id, 
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5,          # just the 5 most recent
    }
    r = requests.get(url, params=params, timeout=20)
    r.json()["requests"]["data"]
    return [(row["period"], float(row["value"])) for row in rows]

    
