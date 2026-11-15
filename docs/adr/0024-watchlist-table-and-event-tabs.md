# 0024 – Watchlist table, event tabs and more event types (supersedes the layout in 0023)

* Status: accepted
* Date: 2026-11-15

## Context
The card-based watchlist from 0023 still read as a long page. Its groups
("developing stories", "waiting for confirmation", "also in the news") were
not categories a financial user filters by. Each card had too many fields
("Status", "Evidence", "News confirmed?"), and the expected and measured
reactions were shown twice in two separate sections. Only three event types
existed.

## Decision
* **Words:** a chain of related news is an **event**; each step is an
  **update**. "Story" and "outlet" are no longer shown; news providers are
  **sources**.
* **Home = one compact, paged watchlist table** (12 rows per page), the habit
  of Bloomberg and Reuters terminals:
  * four key numbers on top: companies tracked, events, unusual stock moves,
    news sources;
  * filters a financial user expects: market (US / Australia), **GICS
    sector**, with events / all companies, search;
  * columns: Company · Sector · Latest event · Stock vs index · Sources.
* **Stock vs index** is one figure with its context: "−18.5% vs S&P 500 ·
  9 Nov–12 Nov · Unusual move". The industry concept is excess return over a
  benchmark; "unusual" means the event-study z-test is significant.
* **Sources** replaces "News confirmed?": the number of independent sources
  and their average reliability score.
* **Event page with tabs:** Overview (price chart + suggested actions),
  Updates, Expected vs actual, Analyst data. Four key numbers sit above the
  tabs.
* **Expected vs actual is one scorecard:** one row per update, one column per
  market measure (share price, trading volume, price swings). Each cell shows
  the expected direction, the measured value and ✓ / ✗. "How it works" uses
  the same grid for each event type, with its track record.
* **How it works has three tabs** (News sources, Event detection, Market
  reaction). Each is "How we decide" (the rule) and "The data"; the repeated
  "What we do" text is gone.
* **Eight event types:** Leadership change, Product safety, Takeover, plus
  Earnings beat, Earnings miss, Cyber incident, Job cuts and Supply
  disruption. Each new type is on the list of price-moving firm news in the
  research (earnings, cyber breaches, layoffs, supply shocks); each window has
  its stated reason in `playbooks.json`.
* **Sector is data:** each company in `entities.json` carries its GICS sector.

## Consequences
+ The home page fits on one screen; filters replace scrolling.
+ Expected and actual reactions are read once, in one place.
+ A new event type is a data change (taxonomy + playbook).
- The new types start from judgment priors and need observed events before
  their windows and expectations are calibrated.
