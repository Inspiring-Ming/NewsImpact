"""ALERTS - tell followers when something changes for a company they follow.

After each monitor round the app hands over a snapshot of every event; the
module compares it with the previous one and sends an alert for: a new event,
an event that becomes confirmed, an unusual stock move once measured, and a
new update. The first round only records a baseline (no flood of old news).

Followed companies are kept here too (one list for now: a single user).
Publishes: nothing (talks to people through a Notifier, e.g. Discord)
Consumes:  snapshots passed in by app/monitor.py
"""
