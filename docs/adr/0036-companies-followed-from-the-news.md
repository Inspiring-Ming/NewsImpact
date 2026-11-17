# 0036 – Which companies we follow: decided from the live news, within the S&P 500 and ASX 200

* Status: accepted
* Date: 2026-11-17

## Context
We followed a hand-picked list of 73 companies (40 US, 32 ASX, TSMC). Its stated reason
("the largest, most-covered") was not a rule anyone could repeat, and the list did not
change with the news.

## Decision
* **Universe** (`data/reference/universe.json`, ~700): every S&P 500 and S&P/ASX 200 member.
  Reason: each has a benchmark to measure against and daily prices from our vendor. Built by
  `scripts/refresh_universe.py` from Wikipedia's constituent lists (CC BY-SA 4.0), refreshed
  quarterly after the index reviews. `entities.json` keeps how the news writes some names
  and may add a company outside the indexes only with a `why` (TSMC, Atlassian).
* **Names**: index members' names without the legal form ("Alphabet Inc." → "Alphabet"),
  matched only as written; `ambiguous_names` (e.g. "ASX", "Nasdaq", "Dow", "Target", "Seek")
  are never matched alone. All names are one combined pattern (sentence-extractor-v3), so
  700 companies cost no more time than 73.
* **Following** (`app/following.py`, `methodology.json` "following", each number with its
  reason): followed once 3 articles name a company within 7 days; kept for 30 days after
  its last article or event; companies users follow always; at most 150, most named first.
  The first decision starts from what the website showed, so nothing disappears at once.
* **Cost gate**: only followed companies get their own feed each round and have their
  sentences read by the AI; the others are only name-matched (free). Each round also reads
  the feeds of 30 other index members in turn ("discovery"), so each is checked about daily.
  Newly followed companies have their last 7 days of articles read at once.

## Consequences
* Measured on the stored articles (2026-11-17): 107 followed, the 73 plus 34 US companies
  the news was about that week (Berkshire Hathaway, Blackstone, Morgan Stanley, Home Depot,
  Sandisk, ServiceNow...). ASX companies stay while they have news; quiet ones drop after
  30 days and return when the news names them again.
* AI cost grows with the followed count (about US$1.5 a month for 73; expected US$3–4 at
  ~150), inside the US$5 cap; the cap and the per-round call cap still apply.
* Wrong name matches remain possible; the AI's subject check still decides whether an
  event is about the company, and `ambiguous_names` is data to extend.
