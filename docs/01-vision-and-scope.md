# Vision & scope

## Problem
Markets react to news before anyone knows whether it is true. Existing
sentiment tools score *tone*, not *credibility* or *which part of a business*
is affected – so users can't tell a durable signal from a rumour that will
reverse.

## Product (first version)
**Reliability-adjusted news impact**: for each news item, show
(1) how trustworthy the source and each claim are, (2) which companies and
which business aspects are affected – including suppliers, customers and
competitors, and (3) how the market actually reacted, historically and now.

## First target clients (choose one to start)
* Small/mid hedge funds & prop desks – signals API, backtests.
* Corporate investor-relations / risk teams – "what is being said about us and
  suppliers, and does it matter?" alerts and reports.
* Research / media analytics – source-credibility analytics.

Pick one beach-head; it decides latency, data and compliance requirements.

## MVP scope (in)
One sector (e.g. US semiconductors or ASX top 50), ~10–20 sources, daily
batch + near-real-time ingest, reliability scores, impact map, event studies,
a web report, and an API.

## Out of scope (for now)
Automated trade execution, personalised investment advice, intraday
tick-level analytics, social-media firehoses.

## Data sources & licensing (decide before building connectors)

| Data | Free / low-cost options | Commercial use caveat |
|---|---|---|
| News | GDELT, company RSS/press releases, SEC EDGAR filings | Many outlets' terms forbid storing/redistributing full text – store metadata + derived features; license feeds for production |
| Market data | Vendor APIs with commercial tiers | Unofficial website scrapers are **not** licensed for commercial products |
| Reference data | SEC company tickers, OpenFIGI, GLEIF (LEI) | Generally permissive |

## Regulatory note
Analytics and research tools are generally lower-risk than personalised
advice; get local legal advice before marketing "trading signals" to
retail investors. Always include disclaimers and an audit trail.
