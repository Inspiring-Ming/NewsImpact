# 0031 – Project review: one place per concern, nothing unused

* Status: accepted
* Date: 2026-11-16

## Context
After many rounds of product changes, a full review checked every folder and
file for a stated reason, for code that nothing uses, and for how easy it is
to add or change a function, a service or a page.

## Decision
* **Removed** the `impact` module (supplier/peer spillover). In the live
  system it had no relationship data, nothing on the website used it, and it
  only repeated each claim's tone. Its event schema, endpoint, demo data and
  tests went with it; the roadmap brings it back with real supplier data.
* **Removed** unused fields and helpers: event `confidence` (replaced on the
  website by Confirmed / Not yet confirmed), `said_by`, `ongoing`; website
  helpers `Pill`, `describe`, and a second copy of the per-type track record
  (the server's is the only one now); unused style rules.
* **`app/views/`** replaces the 480-line `queries.py`: `companies.py`
  (companies and events), `guidance.py` (priority, checks), `briefs.py`
  (three-line briefs), `system.py` (overview, coverage, accuracy). Tests
  follow: `tests/app/`.
* **Adding a module needs no list edits** beyond the import rules: event
  schemas are exported from every module that declares `PUBLISHES`.
* **Website shared parts**: the three small badge components became
  `shared/badges.tsx`; styles are grouped as tokens and base, shared building
  blocks, then one group per page, with phone rules in one block at the end.
  Old and new styles rendered the same 12 views identically.
* **Logs never carry secrets**: every line is redacted for `api_token=` style
  keys and Discord webhook paths (the HTTP client logs request URLs).
* **Docs** (README, architecture, roadmap, settings) describe the current
  product and list how to extend each part; `make docker` uses `.env` and
  keeps state, as the README says.

## Consequences
+ Each concern has one file, and each extension has one documented place.
- Supplier/peer impact must be rebuilt when real relationship data arrives.
