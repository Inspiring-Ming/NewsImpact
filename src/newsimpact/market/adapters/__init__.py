"""Technology behind the market ports - one file per technology.

synthetic.py  deterministic fake prices and volumes for the demo (NOT market data)
eodhd.py      end-of-day prices for US and ASX from EODHD (API key; commercial licence for clients)
csv_file.py   prices from CSV exports of any licensed vendor (reproducible snapshots)
cached.py     wraps any of the above with a SQLite cache (fewer API calls, faster)
"""
