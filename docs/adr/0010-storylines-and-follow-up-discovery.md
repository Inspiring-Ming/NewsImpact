# 0010 – Storylines with playbooks, and automatic follow-up discovery

* Status: accepted
* Date: 2026-11-14

## Context
Market impact often comes from a *sequence* of related news (apology ->
CEO departure -> successor), not from one article. Later stages may never
appear in the feeds we subscribe to. Clients need to see the chain, which
decisions each stage typically triggers, and how markets reacted.

## Decision
* Semantics tags each claim with an `EventType` (semantic trigger).
* A `storylines` module links claims about the same ticker into a
  storyline using **playbooks** – curated JSON describing stages, triggers,
  expected decisions (actor, decision, market channel, direction, horizon)
  and the search terms that signal the next stage.
* Each update publishes `StorylineUpdated` with a `FollowUpRequest`;
  the sources module (`SourcesService.follow_up`) runs targeted searches (`NewsSearch` port:
  fixture now, GDELT live) and feeds discoveries back into the pipeline.
* Linking v0.1 is deterministic (ticker + playbook + 30-day window).

## Consequences
+ Explainable to clients; analysts improve playbooks without code changes.
+ Discovery finds the next chapter even when no subscribed feed carries it.
− Keyword retrieval is high-recall/low-precision; precision comes from the
  semantic classification step (and, next, an LLM analyzer).
− Deterministic linking misses paraphrased links → next: embedding
  similarity + LLM adjudication behind the same service.
