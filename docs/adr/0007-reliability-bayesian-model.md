# 0007 – Bayesian (Beta-Binomial) source reliability as baseline

* Status: accepted
* Date: 2026-11-14

## Context
Reliability must be explainable to clients, work with little data, and
express uncertainty.

## Decision
Per (source, topic) Beta posterior: prior by source type, updated by claims
later confirmed or refuted. Claim reliability = noisy-OR over independent
sources × speculation penalty. Pure functions in `src/newsimpact/reliability/logic.py`.

## Consequences
+ Transparent, with confidence intervals; new sources start at a sensible prior.
− Priors are expert judgement until calibrated on resolved claims.
Revisit with hierarchical models / learned features once ≥ 1,000 resolved claims exist.
