# 0022 – Website: briefing first, two pages, built to grow

* Status: accepted (refines 0020)
* Date: 2026-11-15

## Context
The first website had six technical pages: overview, storylines, outlets,
calibration, quality and method. It read like an internal tool. The product
will be shown to clients and later linked from the company website, so it
must explain itself and stay easy to extend.

## Decision
* **Two pages plus a story view.**
  * *Briefing* (home): what the product does, and story cards, served by a
    single `/v1/briefing` call.
  * *Story*: "in short", then the price reaction, then the stages and their
    evidence; statistics are collapsed.
  * *How it works*: sources, accuracy, track record, and settings with
    reasons.
  * Operations are reduced to a header status pill with "Update now".
* **Plain English everywhere.**
  * `web/src/shared/labels.ts` is the only place that turns codes into words.
    Unknown codes fall back to a readable form, so new event types need no UI
    change.
  * Validation writes its suggestions in plain language too.
* **Built to extend.**
  * One route table (`routes.tsx`) and one folder per page (`features/<page>`).
  * The story page is a list of sections and the method page is a list of
    tabs. A new analysis step, for example analyst revisions, is one section
    component and one list entry.

## Consequences
+ A client can understand a story without knowing the method; analysts still
  get the statistics under *Details*.
+ The briefing page makes one request and never triggers market-data calls:
  it uses stored assessments.
- Old deep links to the six pages no longer work (the site was unreleased).
