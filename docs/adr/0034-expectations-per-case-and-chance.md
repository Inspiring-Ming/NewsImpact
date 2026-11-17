# 0034 – Share price expectations per case, judged against chance; How it works explains every number

* Status: accepted
* Date: 2026-11-17

## Context
The How it works page showed numbers readers doubted, and some were wrong:
* **One expectation per event type.** Takeover was always "rises", but most of our
  takeover events are the company *buying*, and research finds buyers' shares move
  little (Andrade, Mitchell & Stafford 2001). Leadership was always "falls", even for a
  planned CEO appointment (CSL, Oct 2026).
* **"Moved as expected" counted any move in the right direction**, even −0.1%, so a
  coin flip scored about half and nobody could tell whether a result meant anything.
* **Source scores without the sum behind them**: Yahoo Finance at 49% read as "wrong
  half the time"; it means most of its reports were not repeated by another outlet.
* **"Usual updates"** were research-based possible steps, not something we measured.

## Decision
* **Expectations per case**, as reference data (`playbooks.json` "expectations", each
  with its finding and source): the company's part in a deal (target ↑, buyer → little
  change, seller ↑ (Jain 1985), unclear ↕), the results reading (better ↑, worse ↓,
  mixed ↕), or how the event started (leader under pressure or stepping down ↕;
  planned succession → little change, Clayton, Hartzell & Rosenberg 2005). Without
  one, the opening stage's price expectation applies. Job cuts now expect a fall, as
  the research it cites (Worrell, Davidson & Sharma 1991) finds.
* **The company's part in a deal** (`semantics/logic.py` `deal_role`): from where its
  names stand in deal wording, with the cue words in `taxonomy.json` "deal_*" (no
  code to extend). Checked on the 25 live takeover events; unclear stays unclear.
* **Judged against chance** (`views/guidance.py` `group_record`): up/down = moved that
  way (chance 1 in 2); "a larger move than usual" = unusual (1 in 20); "little change"
  = not unusual (19 in 20). A verdict (matches / no clear pattern / goes against) only
  from `min_events_for_calibration` (20) events, by a binomial z-test at
  `significance_z`, both in `methodology.json` with their reasons.
* **How it works** reads one snapshot field per round (`/v1/event-types`): events and
  confirmed per type, how many events reached each possible step, the median gap,
  and the cases. Source scores show their sum in words; starting estimates and their
  reasons come from `reliability/logic.py` (`PRIOR_WHY`, via `/v1/method`).
* Wording: "usual updates" became "updates so far" and "possible next step".

## Consequences
* Every number on the page says where it comes from; no new files beyond this record.
* Today no case has 20 measured events, so every verdict reads "too few to judge":
  honest, and it will change as events accumulate.
* A role read wrongly gives a wrong expectation for that event; the cue lists are
  data and the tests use real headlines.
