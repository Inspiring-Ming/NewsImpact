# 0028 – Primary user, verified events vs unverified signals

* Status: accepted
* Date: 2026-11-16

## Context
We had not named who the product is for, so every page tried to serve
everyone. A count on 2026-11-16 showed 1 of 54 events backed by more than
one source, and several "events" were opinion or feature pieces (for example
"How Nvidia's scandal knocked thousands off your 401(k)" read as an earnings
miss). For a professional, one false alarm costs more trust than ten correct
events earn.

## Decision
* **Primary user:** professional equity investors (analysts and portfolio
  managers at small and mid-sized funds, family offices, serious
  self-directed investors) who follow a list of stocks. Second: investor
  relations teams watching their own company. Retail investors later, with
  care about anything that reads as advice.
* **What they need, in order:** does anything I follow need attention; is it
  real; has the market reacted; what usually happens next; tell me when it
  changes. The pages follow that order.
* **Verified events vs unverified signals.** Verified = an update reported by
  2+ independent sources, or published by the company itself (press release)
  or in an official filing. Wording that only quotes the company does not
  count: one article is still one source, and the attribution reading can be
  wrong. The home page opens on verified events (or "My companies" once any
  are followed); unverified signals are one click away and labelled.
* **Commentary is not an event.** An article whose headline or opening
  sentence reads as opinion, explainer, interview or feature
  (`taxonomy.json` → `commentary`) opens no event. Seven existing events built
  only from such articles were removed from the local database (backup kept);
  one mixed event was left as is.
* **My companies:** a star per company, kept in the visitor's browser until
  accounts exist.
* **Traceability:** every headline and every update links to the original
  article; the event page states how fresh prices are (daily closes, last
  close date) and that news is checked hourly.
* **Provisional move:** while the measurement window is open, the stock's move
  against its index up to the latest close is shown, labelled provisional.
* **History next to the event:** "past events of this type we measured" with
  the average move and how often it went the expected way, flagged as a
  first indication below 20 events.

## Consequences
+ The default view is small but trustworthy (today: Nvidia only).
+ The gap is now visible and measurable: more corroborating sources (a news
  wire, ASX announcements) would turn signals into verified events.
- Followed companies live in one browser; alerts and accounts come later.

## Follow-up (same day): simpler, factual labels
* A separate "Verified events" view and an "All companies" view repeated the
  event list. Now there are two views: **All events** and **My companies**;
  search also finds companies without an event.
* The confidence percentage is no longer shown. Readers found the
  calculation hard to accept, and two checkable facts say the same thing:
  **Confirmed** (2+ independent sources, a company press release or a
  filing) or **Single source**, with the source names on hover. Reliability
  stays on How it works, where its track record is shown.
* "What the news says" (tone, fact or rumour, who said it) shrank to two
  chips inside the event cell: good or bad news, and a rumour flag only when
  it applies. "Who said it" repeated the sources column.
* Every event now shows its stock move and trading volume, measured even
  when the event type's playbook expects no reaction in that measure; recent
  news says "too early" instead of "no data".
* "Developing / Complete" became "x of y usual updates · next to watch: ...".
* Expected vs actual opens with a reaction scorecard: one coloured tile per
  update and measure (✓ as expected, ✗ opposite, – no clear move, … too
  early), above the detailed bars. Bars grow in when a page opens, unless
  the reader has turned motion off.
