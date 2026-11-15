# 0015 – Automatic monitoring with SQLite persistence (Postgres later)

* Status: accepted (CLI loop replaced by the server's monitor: 0020)
* Date: 2026-11-15

## Context
Monitoring outlets means repeated rounds, and state must survive restarts:
seen articles, outlet track records, open storylines and pending follow-up
searches. Before this decision, everything was in memory.

## Decision
* One monitoring round is `sources.collect()` followed by `sources.follow_up()`
  (`app/monitor.py`). The schedule is a deployment choice: the
  `newsimpact monitor` loop locally, EventBridge Scheduler → Lambda on AWS.
* Articles from all outlets are processed in publication order, so
  storylines follow the real chronology.
* Failures are isolated: a failing feed or search is logged and retried next
  round.
* Every stateful port has a `memory` and a `sqlite` adapter, selected by
  `NI_STORE`. SQLite is one file, needs no server and costs $0. Adapters
  share `shared/sqlite.py`, and business logic may not import it.
* GDELT requests are spaced at least 5 s apart and back off on HTTP 429.

## Consequences
+ A laptop or one small server can monitor the outlets continuously at $0.
+ Moving to Postgres means adding one adapter per storing module, with no
  business-code changes.
− SQLite allows only one writer process at a time; use Postgres before
  running several workers.
