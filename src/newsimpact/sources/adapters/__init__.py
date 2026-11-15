"""Technology behind the sources ports - one file per technology.

json_file.py  SourceRegistry read from sources.json
rss.py        Feed for RSS 2.0 / Atom (most news sites)
gdelt.py      NewsSearch over the free GDELT DOC 2.0 API
fixture.py    Feed + NewsSearch over local demo files (no network)
memory.py     stores in memory (demo, tests)
sqlite.py     the same stores on SQLite (monitoring; survives restarts)
"""
