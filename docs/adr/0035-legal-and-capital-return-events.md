# 0035 – Two more event types: Legal & regulatory, Dividends & buybacks

* Status: accepted
* Date: 2026-11-17

## Context
We followed 7 event types. A check of all 2,752 stored articles (rules reading, free)
for market-moving news those types miss found:

| Candidate | Articles / companies | Decision |
|---|---|---|
| Regulator action or lawsuit on its own | 41 / 13 (Intel shareholder suits after a 29% fall, Meta's €805m Italy fine, Nvidia DOJ probes, ASIC suing CBA) | **added** |
| Dividend or buyback change | 11 / 7 (Costco special dividend and $4bn buyback, ExxonMobil raise and $20bn buyback) | **added** |
| Analyst rating change | 16 / 14, mostly opinion pieces or naming the bank instead of the company | not now: opinions, not company events |
| Drug approval, capital raising, credit rating, index change, strike | 0–3 each | not now: too rare for our 73 large companies |

Regulator actions and lawsuits were already recognised, but only continued an open
product safety or cyber event.

## Decision
* **Legal & regulatory** (`legal_regulatory`): opened by `regulatory_action` or
  `litigation`, ended by the new `legal_resolution` (settled, fine agreed, ruling,
  dropped). An open product safety or cyber event of the company still takes its own
  regulator and lawsuit steps first. Window 180 days. Expected: a fall (regulator:
  Karpoff, Lee & Martin 2008; lawsuit: Bhagat, Bizjak & Coles 1998).
* **Dividends & buybacks** (`capital_return`): `capital_return_up` (raise, special,
  start, buyback) and `capital_return_down` (cut, suspend), read as raised / cut /
  mixed. Window 30 days. Expected: raised ↑, cut ↓ (Michaely, Thaler & Womack 1995;
  Ikenberry, Lakonishok & Vermaelen 1995).
* Law-firm adverts inviting investors to join a class action are commentary (taxonomy
  cues and the classifier prompt), so they cannot open legal events.
* Every stored article was re-read with taxonomy v9 (about US$0.2 of AI).

## Consequences
* Two more types on the website, each with its reason and research; no code beyond
  data, one prompt line and tests (the playbook design already allowed it).
* A shareholder suit filed after a big fall follows the fall: its "move" is partly the
  cause, not the effect. The event page shows the dates; the expectation stays the
  research one.
