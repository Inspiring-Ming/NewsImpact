# 0011 – Start with a curated list of outlets; grow it by configuration

* Status: accepted
* Date: 2026-11-14

## Context
Reliability scores are only meaningful for outlets whose track record we
follow over time. Reading "the whole web" from day one gives thousands of
outlets with no history, so their reliability would be noise. The product
should start with a few well-understood outlets and add more as clients ask.
Before this decision, outlets were created implicitly whenever an article
arrived, and the web search accepted any domain.

## Decision
* The outlets are a **curated list**, `data/reference/sources.json`: id, name,
  type (sets the starting reliability), domains, country, feeds, enabled.
  The fictional demo uses the same format in `data/demo/sources.json`.
* Every listed outlet is registered at start-up, so it shows up in the
  reliability leaderboard before its first article arrives.
* `sources.collect()` reads every feed of every enabled outlet. A broken
  feed is logged and skipped.
* Follow-up search is **restricted to the listed outlets' domains**. Other
  outlets are ignored unless `NI_ACCEPT_UNLISTED_SOURCES=true`. Unlisted
  outlets are then marked `listed=false` and get the "unknown" prior.
* Each feed names a `kind` (`rss`, `fixture`, …) that selects an adapter in
  `app/wiring.py`. Unknown kinds fail at start-up.
* Starter list: BBC, Guardian, NYT, CNBC, MarketWatch (major outlets),
  PR Newswire (company press releases), SEC EDGAR 8-K (filings; disabled
  until a contact User-Agent is configured).

## Consequences
+ Adding an outlet is a one-row change; a new feed technology is one
  adapter file plus one wiring line.
+ Reliability, coverage and licensing questions are scoped to a known list.
− Free RSS gives headlines and summaries, not full text. Wire services
  (Reuters, AP, Dow Jones) need licensed adapters.
− Publisher terms must be checked before showing content to paying clients.
Revisit when clients need coverage beyond the list. The switch already
exists; what would be added is automatic promotion of frequently seen
unlisted outlets.
