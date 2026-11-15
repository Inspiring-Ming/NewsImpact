"""SHARED - the small toolkit every module uses.

events.py  base classes for data and events, and the event envelope
bus.py     how modules talk to each other (publish / subscribe)
text.py    text normalisation and stable ids

Kept deliberately tiny: if only one module needs something, it lives in that
module. Imports nothing else from newsimpact.
"""
