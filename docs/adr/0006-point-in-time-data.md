# 0006 – Point-in-time, versioned data

* Status: accepted
* Date: 2026-11-14

## Context
Finance clients will reject any result contaminated by look-ahead bias,
and regulated users need audit trails.

## Decision
Every record carries `published_at` (event time) and `ingested_at`/`as_of`
(knowledge time); every derived output carries `model_version`. Data is
append-only; corrections are new records. Backtests query "as of" a time.

## Consequences
+ Credible backtests, reproducibility, auditability.
− More storage and slightly more complex queries.
