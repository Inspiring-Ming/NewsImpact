# 0030 – What we tell the user: priority, what to check, three-line briefs

* Status: accepted
* Date: 2026-11-16

## Context
Users asked what the site should tell them and what they should do now.
Practice: Bloomberg's Terminal opens company news with an AI summary of three
bullet points; AlphaSense pairs alerts with AI "Smart Summaries"; trading
desks triage incoming news by severity, relevance, source authority and time
sensitivity. Rules: in Australia, factual information needs no licence while a
recommendation is financial advice (ASIC RG 244); US publishers keep the same
line. So we say what to check, never what to buy, sell or hold.

## Decision
* **Priority per event** (`app/guidance.py`): Act now = confirmed news with an
  unusual move or a new update in 24 hours; Check = confirmed news otherwise,
  or an unusual move not yet confirmed; Background = the rest. Shown on every
  row, on the event page, and in a **Needs your attention** strip (up to three
  events, followed companies first) with each event's most useful next step.
* **What to check now**: a short checklist from rules: read the original;
  look for confirmation; review position size after an unusual move; when the
  stock reaction becomes final (counted in weekdays); the next usual update;
  compare sector peers. Tested to contain no advice words.
* **Three-line brief** (what happened, what the market did, why it matters),
  written by the economy language model from facts we hold, during the monitor
  round only. Checked before use: no advice words and no number absent from
  the facts; otherwise a rules-written brief from the same facts. Facts are
  hashed, so unchanged events are never re-written. Measured on 2026-11-16:
  46 briefs for $0.0086 (about $0.0002 each), 1 rejected by the checks.
* **Alerts carry the brief** and the next step.
* **Track record per event type** is computed on the server and shown beside
  each event.

## Consequences
+ Every event answers "how urgent, what happened, what to check" in one place.
- Rules for priority are judgment calls; revisit them with user feedback.

## Follow-up (2026-11-16)
The "Needs attention" strip above the key numbers made the home page long. It
is now a sub-tab of both views (All events, My companies): **Needs attention**
(every Act now / Check event in the view, most urgent first) and **All** (the
impact map and the table). Filters apply to both tabs.
* Renamed **Priorities** and moved after **All** (the default tab). Shown as a
  board with one column per level ("Act now", "Check"); each card shows why it
  is there (reason, stock move bar, sources and confirmation, tone, rumour) and
  the next step. Levels are defined once in `web/src/shared/priority.ts` (name,
  order, meaning, whether they get a column), read by the badge and the board.
