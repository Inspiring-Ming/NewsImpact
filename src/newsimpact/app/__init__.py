"""APP - settings, wiring and the entry points (HTTP API + website, monitor).

config.py   deployment settings from NI_* environment variables (.env)
wiring/     picks the technology behind every port (the only place that does);
            plugins.py has one table per kind of technology
api/        versioned JSON API (/v1), one router file per area, and the website at /
monitor.py  the hourly round: collect, follow up, check evidence, briefs, alerts
demo.py     loads the fictional demo data through the real pipeline
logs.py     JSON logging
views/      what the website and API show, composed from the modules
            (companies and events, priority and checks, briefs, system status)

The only package allowed to import adapters. Rules about news and markets
belong in a module; views/ only holds rules about what to show a reader first
(priority, checklist), kept small and documented in ADR 0030.
"""
