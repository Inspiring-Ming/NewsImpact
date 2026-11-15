"""VALIDATION - check each storyline against independent evidence, then conclude.

For every stage of a storyline it asks two questions:
  1. Is the claim true?  How many independent listed outlets reported it,
     and did an authoritative source (filing, company statement) confirm it?
  2. Did the expected decisions happen?  For each decision the playbook
     expects (e.g. "price down", "volatility up") it looks at what the market
     actually did, using the market module's measurements.
It then writes a conclusion, a confidence level and suggestions, stamped
with the versions of everything used, so results can be reproduced. Every
monitoring round re-assesses open storylines (checks that were "pending" mature
as market data arrives) and keeps the history.

Across many storylines, calibrate() tests whether each stage really moves each
channel (BMP cross-sectional test) and whether link windows fit the observed
gaps between stages - turning playbook priors into measured facts.
All thresholds: data/reference/methodology.json, each with its reason.

Extend it: a new kind of evidence (credit spreads, analyst revisions,
filings) = a new MarketEvidence channel or a new port here. Rules for
conclusions live in logic.py.

Publishes: nothing (queried by the API and the monitoring round)
Consumes:  nothing (reads storylines handed to it)
"""
