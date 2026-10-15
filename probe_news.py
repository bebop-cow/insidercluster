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

import subprocess
def notify(count):
    msg = f"{count} AI-debt distress headlines flagged — review bubble scan"
    subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "Bubble Watch"'])

def main():
	hits = scan()
	show_scan(hits)
	

if __name__ == '__main__':
	main()


