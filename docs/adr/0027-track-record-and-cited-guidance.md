# 0027 – Source track records, cited guidance, visual cells

* Status: accepted
* Date: 2026-11-16

## Context
* Source reliability never moved in the live system: nothing recorded
  whether a source's reports turned out right, so every source kept the
  fixed starting value for its type and the numbers looked arbitrary.
* "Suggested actions" were status notes from the checks ("2 reactions need
  more trading days"), not guidance a reader could act on or trace.
* The watchlist, the expected-vs-actual grid and the analyst data were text
  and codes (CAR, z, file hashes); on phones the table was cut off.
* The accuracy check needed a button press and did not say what it was for.

## Decision
* **Track record by corroboration.** A report is "confirmed" when another
  independent origin reported the same update, and "unconfirmed" when nobody
  did within 7 days (younger reports are not judged). Unconfirmed counts
  half, because "nobody else reported it" is weaker than "shown wrong".
  This follows truth-discovery research: sources whose claims others
  corroborate are more trustworthy (Yin, Han & Yu 2008). Settings and
  reasons: `methodology.json` → validation `confirmation_days`,
  `unconfirmed_weight`. Recomputed every round, so it is never double
  counted.
* **One starting rule for all source types:** each starts with its type's
  estimate (filing 95%, agency 80%, newspaper 75%, press release and
  aggregator 67%, ordered by how content is checked before publishing),
  worth 10 reports of evidence; after 10 judged reports, record and estimate
  weigh equally.
* **Confidence uses current reliability:** validation re-scores every report
  with its source's reliability today, so an event's confidence and its
  sources' scores always agree.
* **"What to know" replaces "Suggested actions":** what we measured (from
  data), what research shows usually happens next (each finding with its
  published source, in `playbooks.json` → `research`), and what investors
  check next (common analyst practice, `playbooks.json` → `watch`). No LLM
  writes this text: every statement stays traceable to data or a citation.
  An LLM case summary can be added later on top of these facts.
* **Visual cells everywhere:** a move bar from a centre line, a ratio bar
  with a 1× tick, a confidence meter, source dots and update-progress dots,
  each next to its number in words. On phones each watchlist row is a card.
* **Lead event per company** is the best-supported one (2+ sources), then the
  most recent, so a single-source misreading cannot hide a confirmed event.
* **"How we measured"** replaces raw analyst data: plain measures, results,
  "x times a typical move", and the method in four sentences; file
  fingerprints are folded away for exact repetition.
* **Accuracy check** shows automatically (computed once per server start)
  with a one-line purpose.

## Consequences
+ Reliability differs by source for a reason the reader can check (e.g.
  Yahoo Finance: 8 of 35 reports confirmed, 47%).
+ Guidance is grounded in published research, with the source shown.
- Single-source scoops are penalised until others report them; the half
  weight limits this, and calibration can revisit it as data grows.

## Follow-up (same day)
* The home page's key numbers open a detail panel when clicked: events by
  day, ranked stock moves (bars from a centre line), and articles in the last
  24 hours by source and by company.
* The event page has three tabs. "What to know" was too long beside the
  chart: Overview now shows the chart, then two short cards (watch next; one
  research finding with its source, more on request). Updates is a timeline.
  "How we measured" merged into Expected vs actual, where each measure is
  defined in a sentence on the page and each bar is drawn against the stock's
  normal range (±1.96 typical moves), so "unusual" is visible, not just named.
* Watchlist columns have fixed widths (they shifted with each page's text);
  rows without an event show their latest news across the empty columns.
