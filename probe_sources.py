import requests

HEADERS = {"User-Agent": "Lazuli Research tyrin@example.com"}

def probe_sec():
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {"forms": "4", "q": "purchase"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        print("SEC status:", r.status_code)
        print("SEC sample:", str(r.json())[:300])
    except Exception as e:
        print("SEC FAILED:", e)

def probe_congress():
    url = "https://www.bargo.ai/free-apis/congress/v1/trades"
    try:
        r = requests.get(url, params={"ticker": "NVDA"}, headers=HEADERS, timeout=20)
        print("\nCongress status:", r.status_code)
        print(r.json()["trades"][0])
    except Exception as e:
        print("\nCongress FAILED:", e)

probe_sec()
probe_congress()
