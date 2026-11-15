# 0017 – Count independent origins, not outlets: attribution and copy detection

* Status: accepted
* Date: 2026-11-15

## Context
The same story reaches many outlets: syndicated copies, light rewrites, and
articles that say "…, Reuters reported". Counting each outlet as separate
confirmation overstates evidence and double-counts impact. Investors also
over-react to reprinted, stale news (Tetlock 2011).

## Decision
* Sources mark **copies**:
  * same text from another outlet, or ≥ 80% shared 5-word shingles within 3
    days, becomes `copy_of`, pointing at the root original;
  * a repeat by the same outlet, or the same URL read again, is dropped.
* Semantics adds an **attribution** step: own reporting, a cited outlet
  (with its id), a company statement, a filing, or anonymous sources. Its
  wording lists live in the taxonomy.
* A background guard keeps history ("has issued several recalls in the
  past") from triggering events.
* Each storyline report carries its **origin**. Validation counts distinct
  origins, and a filing or company statement counts as authoritative.
* Copies get novelty 0.2, so they barely add to impact.
* All thresholds are in `methodology.json` → sources.

## Consequences
+ "Confirmed" means independent confirmation; ten echoes of one scoop are
  one origin.
+ The labelled set measures attribution quality (baseline accuracy 0.96).
− Word-list attribution misses implicit sourcing. The LLM step can improve
  this, measured on the same set.
