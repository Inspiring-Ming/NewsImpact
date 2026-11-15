"""ALERTS - tell followers when something changes for a company they follow.

After each monitor round the app hands over a snapshot of every event; the
module compares it with the previous one and sends an alert for: a new event,
an event that becomes confirmed, an unusual stock move once measured, and a
new update. The first round only records a baseline (no flood of old news).

Followed companies and sent alerts are kept per user (identity module); the
Channels port says where each user's alerts go (SharedChannels: the configured
Discord for everyone, until users have their own).
Publishes: nothing (talks to people through a Notifier, e.g. Discord)
Consumes:  snapshots passed in by app/monitor.py
"""
