# 0016 – Every setting is a reasoned prior, measured and revised

* Status: accepted
* Date: 2026-11-15

## Context
Coverage (which companies, outlets and events), storyline windows,
measurement windows and confirmation thresholds were partly hard-coded
numbers without stated reasons. Clients and reviewers will ask "why 30
days?" or "why these outlets?".

## Decision
* Method settings live in versioned reference files: `sources.json`,
  `entities.json`, `taxonomy.json`, `playbooks.json`, `methodology.json` and
  `llm_prices.json`. Each value sits next to its reason. Deployment settings
  stay in environment variables.
* Every number is a prior with a reason (literature, industry practice or
  stated judgement). It is measured with `coverage`, `evaluate` and
  `calibrate`, then revised by a versioned change.
* Calibration rules are themselves configured:
  * a window suggestion is the 90th percentile of observed gaps × 1.25,
    once there are ≥ 20 gaps;
  * a market-reaction finding needs ≥ 20 events and a BMP cross-sectional
    test.
* Assessments record content hashes of all reference files.
* The full policy is in docs/07-coverage-and-settings.md.

## Consequences
+ Every number can be explained and traced, and changes are reviewable diffs.
+ Priors are replaced by measurements as data accumulates.
− Early on, most findings are "indicative" (few events). That is honest, but
  the sales story must say so.
