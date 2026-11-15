"""Technology behind the alerts ports - one file per technology.

discord.py  sends alerts to a Discord channel (incoming webhook)
shared.py   every user's alerts go to the same configured channels
memory.py   followed companies and sent alerts in memory (tests, demo)
sqlite.py   the same in SQLite, per user (survives restarts)
"""
