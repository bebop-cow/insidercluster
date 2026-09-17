import os
from dotenv import load_dotenv
import requests

load_dotenv()

KEY = os.getenv("EIA_KEY")

def probe_refinery():
    # weekly refinery % utilization, US
    url = "https://api.eia.gov/v2/petroleum/pnp/wiup/data/"
    params = {
        "api_key": KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5,          # just the 5 most recent
    }
    r = requests.get(url, params=params, timeout=20)
    print("status:", r.status_code)
    print(r.json())

probe_refinery()