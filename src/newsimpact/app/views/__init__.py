"""What the website and API show, composed from the modules.

companies.py  companies and their events (the watchlist and event pages)
guidance.py   priority and "what to check now" (rules, no AI)
briefs.py     three-line event briefs (AI from our facts, with a rules fallback)
system.py     overview counts, source coverage, event-type stats, reading accuracy
snapshot.py   what pages read, computed once per round over the pages window
news_data.py  the assistant's data (NewsData port) from the snapshot and the articles
"""
