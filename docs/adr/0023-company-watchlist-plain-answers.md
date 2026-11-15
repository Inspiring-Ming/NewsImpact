# 0023 – Company watchlist with plain answers (supersedes the layout in 0022)

* Status: accepted
* Date: 2026-11-15

## Context
Visitors could not tell what the site was for. The home page showed internal
pipeline counts ("258 articles"), labels such as "Concluded" and "3 of 3",
and "vs market" without naming the market. Only companies with a full story
appeared at all.

## Decision
* **Home = a company watchlist**, the format investors know from Bloomberg
  and Reuters. It lists every company we follow:
  1. developing stories;
  2. stories waiting for confirmation (single source);
  3. other companies in the news;
  4. companies with no recent news.
* **Each story answers four questions in plain words**, written once in
  `/v1/companies`:
  * status ("Settled - new leader named");
  * stock reaction against its named index ("18.5% below the S&P 500 - an
    unusually large move"): the industry concept is excess return against a
    benchmark;
  * whether the news is confirmed ("Yes - reported by 5 outlets");
  * evidence (Strong / Partial / Weak, with the reason).
* **Single-source stories are listed separately** as waiting for
  confirmation, because one outlet can be a misreading (e.g. a film deal read
  as a takeover).
* **How it works** has four tabs, each named in plain words with the
  industry or research term beside it.
* **Names live in data:** companies (name, country, aliases) in
  `entities.json`, now 73 companies (42 US-listed, 31 ASX); story and event
  titles in `playbooks.json`; plain-English expected reactions in the
  playbooks.

## Consequences
+ A first-time visitor can read a card without any explanation.
+ More companies are visible (all 73), not only those with stories.
- Wording lives in the API, so a translation would change it there.
