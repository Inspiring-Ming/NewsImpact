# 0013 – Semantics: taxonomy as data, analysis as a chain of steps

* Status: accepted
* Date: 2026-11-15

## Context
What we look for in news (event types, aspects, word lists) was hard-coded:
enums in `models.py` and lists in the analyzer. Adding a new kind of trigger
or a new measurement meant changing several files, and an LLM analyzer would
have needed its own copy of the labels.

## Decision
* Event types, aspects and word lists live in `data/reference/taxonomy.json`
  (versioned). Event types and aspects are strings validated against it, and
  every playbook trigger must exist in it (checked at start-up).
* Analysis is a chain: one `ClaimExtractor`, then `ClaimStep`s in the order
  given by `NI_SEMANTIC_STEPS`. Each step adds one kind of analysis.
* `Claim.signals` holds open-ended measurements (e.g. `uncertainty`), so new
  steps need no schema change.
* `Claim.model_version` records the extractor and every step, including the
  taxonomy version.

## Consequences
+ Analysts extend triggers without a release; developers add a measurement
  as one class plus one registry line.
+ The same taxonomy can drive word-list and LLM steps, so both can be
  evaluated against the same labels.
− Event types are no longer checked by the type checker; the start-up check
  and tests replace that.
