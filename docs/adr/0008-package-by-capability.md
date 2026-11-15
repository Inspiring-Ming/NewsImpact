# 0008 – Package by business capability, not by technical layer

* Status: accepted (supersedes the code layout in 0001); file template and `contracts/` folder amended by 0012
* Date: 2026-11-14

## Context
The first layout grouped code by layer (`domain/`, `ports/`, `adapters/`,
`modules/`). Understanding one capability meant opening five places; files
such as "all models" or "all in-memory stores" grew without a clear owner;
two capabilities secretly shared one repository.

## Decision
Each capability (ingestion, semantics, reliability, impact, storylines,
market) is a folder containing its own ports, logic and adapters.
Cross-capability types live only in `contracts/` (one file per publisher).
A tiny `kernel/` holds the event bus and text ids. `app/` wires everything.
Each capability keeps its own read models (e.g. reliability builds its own
source registry from `SourceRegistered` events). Five import-linter
contracts enforce the boundaries in CI.

## Consequences
+ One folder = one capability = one future deployable and one owner.
+ No shared mutable state between capabilities.
− Some duplication of small read models – deliberate, it is what allows
  independent deployment.
