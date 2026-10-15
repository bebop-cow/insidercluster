import requests
url = "https://news.google.com/rss/search?q=CoreWeave+debt&hl=en-US"
r = requests.get(url, timeout=10)
print(r.status_code, len(r.text))
print(r.text[:500])

import feedparser
import urllib.parse

def fetch_headlines(query, limit=10):
    q = urllib.parse.quote(query)                    # "CoreWeave debt" -> "CoreWeave%20debt"
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US"
    feed = feedparser.parse(url)
    return [(e.title, e.link) for e in feed.entries[:limit]]

import ollama

def classify(headline):
    prompt = f"""You are flagging news about companies in financial trouble.
Answer YES if this headline suggests ANY of: rising debt costs, bond/credit problems, financing trouble, or investor alarm about debt.
Answer NO otherwise.
Reply with ONLY the word YES or NO.

Headline: {headline}
Answer:"""
    resp = ollama.chat(model="qwen2.5:3b", messages=[{"role":"user","content":prompt}])
    text = resp["message"]["content"].strip().upper()
    return "YES" if "YES" in text else "NO"

WATCHLIST = ["Oracle","CoreWeave","Meta","Microsoft","Google","Amazon",
             "Nebius","Applied Digital","IREN","Nvidia"]

def scan():
    hits = []
    for name in WATCHLIST:
        for title, link in fetch_headlines(f"{name} debt", limit=5):
            if classify(title) == "YES":
                hits.append((name, title, link))
    return hits


