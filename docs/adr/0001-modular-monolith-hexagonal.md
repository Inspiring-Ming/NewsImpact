# 0001 – Modular monolith with hexagonal architecture

* Status: accepted (code layout superseded by 0008)
* Date: 2026-11-14

## Context
We need independent, replaceable parts and future scale, but we are a
startup with a small team and a tight cloud budget. Microservices from day
one would multiply deployment, observability and cost overhead.

## Decision
One deployable Python package with strict internal boundaries:
`domain` ← `ports` ← `modules` ; `adapters` wired only in `platform/container.py`.
Modules communicate only through events. Boundaries are enforced in CI with
import-linter. Observability via structured logs now, OpenTelemetry next.

## Consequences
+ Cheap to run and change; any module can be extracted to its own service
  without code changes beyond wiring.
+ Vendors are swappable by writing one adapter.
− Requires discipline; mitigated by automated import contracts.
Revisit when a module needs independent scaling, runtime or team ownership.
