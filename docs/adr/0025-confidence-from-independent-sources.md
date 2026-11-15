# 0025 – Confidence from independent sources, company news feeds, definitions on hover

* Status: accepted
* Date: 2026-11-15

## Context
* The watchlist showed the *average* reliability of an event's sources. All
  newspapers start at the same 75%, so an event from 1 source and one from 5
  sources both showed 75%, although five independent reports are far
  stronger evidence.
* Only a few of the 73 companies ever appeared, because general business
  sections mention few of them.
* The home page's key numbers (companies tracked, news sources) described the
  setup, not the news.
* "vs" and "Sector" were not explained; How it works repeated rules as text.

## Decision
* **Confidence = noisy-OR over independent origins:** the news is wrong only
  if every independent origin is wrong, so confidence = 1 − Π(1 − r) with r
  the best reliability of each origin. Copies of one origin count once. One
  75% source gives 75%; three give about 98%. An event shows its weakest
  update. Computed in `validation.check_claim` (`ClaimCheck.confidence`).
* **Per-company feeds:** a new feed kind `rss_per_company` reads one URL per
  tracked company (`{ticker}` in the URL). First used for Yahoo Finance
  (US and ASX symbols). A failing symbol is skipped, not the whole feed.
* **Aggregator source type** with a 67% starting reliability, because an
  aggregator mixes original reporting with syndicated opinion.
* **Home key numbers** follow what news-analytics products lead with:
  novelty (events this week), market impact (unusual moves, biggest move)
  and news volume (articles in the last 24 hours).
* **Words:** "Stock vs market" with the sign in words ("worse than the
  S&P 500"); "Sector (GICS)". Every column header, key number and How it
  works title carries its definition on hover, from one glossary
  (`web/src/shared/labels.ts` → `TERMS`). How it works shows data only.

* **"Too early" instead of a blank:** a stock move that is still inside its
  reaction window shows "Too early: check after the next trading day"
  (`stock_move_status`).
* **Sort options:** Latest, Biggest move, Most sources, the orders a market
  user expects from a news screen.
* **Price cache fix:** the cache kept one date range per ticker, and a
  request for an old event replaced the S&P 500 range with one ending months
  earlier, so recent events lost their benchmark. The cached range now only
  grows, and a range that ends before its fetch day is refreshed.
* **Stored assessments from older rules are re-assessed** on read
  (`ValidationService.latest` checks `model_version`).

## Consequences
+ More sources now raise confidence, and copies do not.
+ Every tracked company has its own news stream.
- About 73 feed requests per round instead of 8.
- More events mean more price requests; the free EODHD plan (20 calls a day)
  may leave some events without price data until the next day.
