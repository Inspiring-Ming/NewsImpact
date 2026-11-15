"""RELIABILITY - how much to trust each outlet (per topic) and each claim.

Every outlet starts from a prior set by its type (filing > wire > major
outlet > press release > blog > social) and earns or loses trust as its
claims are later confirmed or retracted. Claims add corroboration and a
penalty for speculative wording.

Publishes: ClaimsScored
Consumes:  SourceRegistered, ClaimsExtracted
"""
