"""MARKET - measure what the market actually did after the news (ground truth).

Event studies (abnormal and cumulative abnormal returns), abnormal volume and
abnormal volatility around each event, after removing what the overall
market explains. Used by validation to check the decisions a playbook expects.

Extend it: a new data vendor = an adapter implementing MarketData; a new
channel (credit spreads, analyst revisions, options) = a port + adapter and
one branch in MarketService.observe().

Publishes: nothing yet (queried by validation and the API)
Consumes:  nothing yet
"""
