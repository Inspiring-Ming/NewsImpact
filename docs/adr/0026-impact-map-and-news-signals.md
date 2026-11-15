# 0026 – Impact map, "what the news says", plain method results

* Status: accepted
* Date: 2026-11-15

## Context
The watchlist spent a whole column on the sector, a fixed label, while the
semantic reading of the news (its tone, whether it is a rumour, who said it)
was computed but never shown. The home page was all tables. "Check for news"
did not say what it did. On How it works, labels such as "Name a tracked
company" and "Followed for" were unclear, and the market reaction tab showed
arrows per update without answering the reader's question: does this kind of
news actually move the stock?

## Decision
* **Sector moves under the company name** as a GICS short name (IT, Comm Svcs,
  Cons Disc...), the abbreviations used on trading screens, with the full
  name on hover.
* **New column "What the news says"** for the latest update: tone (from the
  claim's sentiment, ±0.15 kept neutral), stated as fact or rumour (hedged or
  "sources say" wording), who it comes from (news report, company statement,
  official filing, another outlet, unnamed sources), and the update this kind
  of event usually brings next (from the playbook). Tone and rumour are now
  stored on each update (`StorylineEvent.tone`, `is_rumour`).
* **Impact map** on the home page: a dot plot with one row per sector and
  position = stock move against its market, so the reader sees at once which
  sectors and companies reacted. Size = sources; blue = unusual move, also
  labelled with its ticker so colour is never the only cue; hover for detail,
  click to open. The palette was checked with the dataviz validator (contrast
  and colour-blind separation pass in light and dark).
* **"Update now"** replaces "Check for news", with "Live · updated hh:mm ·
  updates every 60 min" beside it.
* **How it works:** plain column names ("About our companies", "Led to an
  event", "Time window", "Measured gap") with definitions rewritten as one
  logical sentence each; tab 3 is now **"Does it move the stock?"**: per event
  type, the expected share price direction next to the measured average move,
  unusual moves and how often the stock moved as expected.

## Consequences
+ The semantic analysis is visible where decisions are made.
+ Tab 3 doubles as an honest quality check: e.g. "Earnings beat" averaging a
  fall shows that misread events still slip through.
- Updates stored before this change were backfilled once by re-reading their
  articles (58 updates, $0.004 of LLM use).
