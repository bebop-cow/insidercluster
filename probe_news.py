import feedparser
import urllib.parse
import requests
import os
from dotenv import load_dotenv
here = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(here, ".env"))
NTFY_KEY = os.getenv("NTFY_KEY")


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
	seen = set()
	for name in WATCHLIST:
		for title, link in fetch_headlines(f"{name} debt", limit=5):
			if classify(title) == "YES" and title not in seen:
				seen.add(title)
				hits.append((name, title, link))
	return hits

def show_scan(hits):
    if not hits:
        print("No distress headlines flagged.")
        return
    current = None
    for name, title, link in hits:
        if name != current:            # new company — print header
            print(f"\n🔴 {name}")
            current = name
        print(f"   • {title}")

from twos10s30s import fetch_series

def yield_line():
    y10 = fetch_series("DGS10").dropna()
    y30 = fetch_series("DGS30").dropna()
    chg10 = (y10.iloc[-1] - y10.iloc[-2]) * 100      # bp move day-over-day
    chg30 = (y30.iloc[-1] - y30.iloc[-2]) * 100
    return f"10Y {y10.iloc[-1]:.2f}% ({chg10:+.0f}bp) | 30Y {y30.iloc[-1]:.2f}% ({chg30:+.0f}bp)"


import subprocess
def notify(hits):
    names = ", ".join(sorted(set(name for name, _, _ in hits)))
    body = yield_line() + "\n\n" + "\n".join(f"• {title}" for name, title, link in hits)
    requests.post(
        f"https://ntfy.sh/{NTFY_KEY}",
        data=body.encode("utf-8"),
        headers={"Title": f"Distress: {names}"},
    )

def main():
	hits = scan()
	show_scan(hits)
	if hits:
		notify(hits)
	print(yield_line())

if __name__ == '__main__':
	main()


