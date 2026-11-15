# 0014 – Validate storylines with independent evidence before concluding

* Status: accepted
* Date: 2026-11-15

## Context
Playbooks describe the decisions that *usually* follow a stage. Presenting
these as conclusions without checking would be guesswork. Clients need to
see what the evidence says, and the evidence must not come from the same
article.

## Decision
* Storylines record every outlet that reports a stage (`reports`). A repeat
  report from another outlet counts as corroboration, not a new stage.
* The market module measures price (CAR), volume and volatility around
  each stage with standard event-study statistics.
* A `validation` module (query-only) checks each stage. The claim is
  confirmed, corroborated or single-source. Each expected decision is
  consistent, inconsistent, not significant, has no evidence, or is not
  measurable. Validation then writes a conclusion, a confidence level and
  suggestions, using rules in `validation/logic.py`.
* Every assessment carries provenance (component versions and
  reference-data hashes) and a "not investment advice" disclaimer.
* Validation reads market data through its own `MarketEvidence` port.
  `MarketService` satisfies that port in-process, so no module imports
  another module's service.

## Consequences
+ Conclusions are explainable stage by stage and reproducible.
+ New evidence (credit, analyst revisions, peers) plugs in per channel.
− There is no market data in the live profile until a licensed price vendor
  is connected, so live assessments say "unverified".
− Rules are hand-set thresholds; calibrate them in Phase 3 backtests.
