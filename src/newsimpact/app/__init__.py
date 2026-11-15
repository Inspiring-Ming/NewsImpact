"""APP - settings, wiring and the entry point (HTTP API + website).

config.py   deployment settings from NI_* environment variables
wiring.py   picks the technology behind every port (the only place that does)
api.py      versioned JSON API (/v1) and the website (web/dist) at /
queries.py  read-only views for the website, composed from several modules
monitor.py  automatic monitoring (collect, follow-ups, evidence checks, repeat)
demo.py     loads the fictional demo data through the real pipeline
logs.py     JSON logging

The only package allowed to import adapters. Contains no business logic: if
you are writing an `if` about news or markets here, it belongs in a module.
"""
