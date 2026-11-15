# 0003 – Event contracts: CloudEvents envelope + versioned JSON Schemas

* Status: accepted
* Date: 2026-11-14

## Context
Modules must evolve independently and may later be written in other
languages or run on different infrastructure.

## Decision
All integration events use a CloudEvents 1.0-style envelope with
`type = newsimpact.<entity>.<verb>.v<N>`, `correlation_id`, and `tenant_id`.
Pydantic models are the source of truth; JSON Schemas are exported to
`schemas/events/` (from each module's `models.py`) and CI fails on drift. Within a version only additive
changes are allowed; breaking changes create a new version, published in
parallel until consumers migrate.

## Consequences
+ Transport-agnostic (memory, SQS/SNS, EventBridge, Kafka); language-neutral.
− Slight boilerplate per event.
