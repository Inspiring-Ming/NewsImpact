# Research framework: news → human decisions → business & market consequences

This is the intellectual core of the product and what differentiates it from
"sentiment scores". Every module maps to one link in this causal chain.

```
 ① SOURCE           ② CONTENT              ③ HUMAN DECISION          ④ MARKET                ⑤ BUSINESS / REAL ECONOMY
 reliability   ──▶  claims, aspect,   ──▶  attention, belief    ──▶  price, volatility, ──▶  guidance, capex, hiring,
 provenance         novelty, framing,      update, over/under-       volume, liquidity,      financing cost, customer
 track record       speculation            reaction, herding         options, credit         & supplier behaviour
        ▲                                                                   │
        └────────────── outcomes resolve claims & calibrate reliability ◀──┘
```

## ① Source reliability – "should anyone believe this?"

| Signal | How | Status |
|---|---|---|
| Track record per source **and per topic** | Beta-Binomial on confirmed vs. retracted/contradicted claims | ✅ v0.1 |
| Prior by source type | wire / filing / outlet / blog / social | ✅ v0.1 |
| Claim-level corroboration | noisy-OR over *independent* sources | ✅ math, ⏳ claim clustering |
| Speculative language penalty | "reportedly", "people familiar…" | ✅ v0.1 |
| Provenance / originality | who published first; syndication graph (copies are not independent!) | ⏳ |
| Author-level reliability | same model, keyed by author | ⏳ |
| Time decay | older evidence weighs less (exponential forgetting on α, β) | ⏳ |
| Correction & retraction behaviour | outlets that correct quickly earn trust | ⏳ |
| **Market-predictive reliability** | historically, did this source's news move prices *and stay moved*? | ⏳ (key differentiator) |

## ② Content semantics – "what exactly is claimed, about whom, touching which part of the business?"

What we retrieve and analyse, layer by layer. Each layer has a clear owner
and extension point, so "more" means adding a row, not redesigning.

| Layer | What | Today | Extend by |
|---|---|---|---|
| Document | outlet, time, language, headline, summary | RSS headline + summary; GDELT headline | new feed kind (licensed full text, filings) – `sources/adapters/` |
| Mentions | companies → tickers | S&P 500 + ASX 200 names (`universe.json`) plus hand-written aliases (`entities.json`), one combined pattern | entity master (OpenFIGI/GLEIF), people → roles (point-in-time) |
| Claim | one checkable statement per sentence naming a company | `SentenceExtractor` | LLM extractor behind `ClaimExtractor` |
| Event type | the semantic trigger (apology, departure, recall, rumour…) | `taxonomy.json` patterns | add an event type to `taxonomy.json` |
| Aspect | which part of the business (revenue, supply chain, leadership…) | `taxonomy.json` keywords | edit `taxonomy.json` |
| Tone | sentiment, speculation | word lists in `taxonomy.json` | better lists or an LLM step |
| Signals | open-ended measurements, e.g. `uncertainty` | `WordListSignal` | new `ClaimStep` (framing, numeric surprise, forward-looking, novelty) |
| Attribution | own reporting, cited outlet, company statement, filing, anonymous | `AttributionStep` (taxonomy wording) | taxonomy wording or the LLM step |
| Originality | copy of another outlet? (exact or ≥ 80% shingle overlap) | `sources` copy detection | `methodology.json` → sources |
| Background | history vs. new event ("has issued several recalls in the past") | taxonomy `background` words | taxonomy or the LLM step |
| Deal role | the company's part in a deal: buyer, target or seller | `deal_role` (`semantics/logic.py`, taxonomy `deal_*` words) | the LLM step |
| Story | which storyline and stage; which independent origins reported it | `storylines` playbooks | new playbook |

The analysis chain is configured by `NI_SEMANTIC_STEPS` and every claim
records the exact chain that produced it (`model_version`).

## ②+ Storylines – news arrives as chains, not single articles ✅ v0.1

A single headline rarely tells the full story. Impact builds (or reverses)
as related events unfold, e.g. *public apology → CEO steps down → successor
named*, or *recall → regulator probe → class action*. Each **stage** triggers
different decisions by different actors, through different market channels:

| Stage (leadership crisis) | Who decides what | Where it shows up |
|---|---|---|
| Public apology | retail reassesses trust; institutions buy protection; board orders review | volume ↑, implied vol ↑ |
| Leader departure | institutions re-underwrite; analysts revise targets; partners review contracts; competitors poach | price ↓, vol ↑, revisions ↓, peer spill-over |
| Successor named | uncertainty resolves | vol ↓, price re-rates on successor quality |

How the system does it ([ADR 0010](adr/0010-storylines-and-follow-up-discovery.md)):
1. **Semantic triggers** – every claim gets an `EventType` (apology, departure,
   recall, regulatory action, M&A rumour…).
2. **Playbooks** ([data/reference/playbooks.json](../data/reference/playbooks.json))
   define stages, triggers, expected decisions and the terms signalling the
   next stage – editable by analysts.
3. **Linking** – same company + playbook + time window → same storyline;
   escalation and resolution are tracked.
4. **Automatic follow-up discovery** – each open storyline asks the sources module to
   search for its next stages (GDELT live, fixtures in the demo), so later
   chapters are found even if no subscribed feed carries them.
5. **Measured reaction per stage** – event study (CAR) at every stage, so we
   can learn which stages actually move which channels.

Research questions this enables: Is the *departure* or the *apology* the
bigger price event? Does an apology from a reliable source predict
departure (hazard rates)? Do markets anticipate later stages (pre-event
drift)? Does resolution (successor) reverse earlier losses?

## ②++ Validation – check the news against independent evidence before concluding

Playbooks say what *usually* happens. Before the system states a conclusion
it checks each stage with sources that are independent of the original article:

| Question | Evidence | Rule (validation/logic.py) |
|---|---|---|
| Did it really happen? | other listed outlets reporting the same stage; authoritative sources (filings, the company itself) | confirmed / corroborated / single-source |
| Did investors react as expected? | market module: price (CAR, t), volume (abnormal volume, z), volatility (ratio, χ² z) | consistent / inconsistent / not significant / no evidence |
| Real-economy decisions (board, customers) | not yet measurable – flagged for follow-up in filings and earnings calls | not measurable |

Output: per-stage checks, the share of measurable expectations the market
confirmed, a confidence level, a written conclusion and suggestions (e.g.
"wait for a second outlet", "no reaction – probably priced in", "watch for
the next stage"), plus the provenance needed to reproduce it. Next evidence
sources: analyst revisions, credit spreads, options, peer returns via the
relationship graph, and resolved claims feeding back into outlet reliability.

## ③ Human decision-making – the behavioural layer

These are the mechanisms (from behavioural finance) that turn information
into trading decisions. Each becomes a measurable feature or hypothesis:

| Mechanism | What it predicts | Measurable proxy |
|---|---|---|
| **Limited attention** | News on busy days / Fridays is under-reacted to | # competing headlines, day-of-week |
| **Salience & framing** | Vivid/negative framing → larger short-term reaction | framing & emotion scores |
| **Over-reaction to unreliable news** | Low-reliability news moves price then **reverses** | reliability × reversal in AR(+2..+10) |
| **Under-reaction / drift** | Reliable but complex news → slow price drift | post-event drift |
| **Herding / cascades** | Many outlets repeating one story amplifies impact even without new information | syndication count vs. independent corroboration |
| **Negativity bias** | Bad news moves prices more than good news of equal magnitude | asymmetric response by sentiment sign |
| **Uncertainty aversion** | Ambiguous news raises volatility more than it moves price | vol & option-implied vol response |
| **Disagreement** | Conflicting sources → higher volume, dispersion | cross-source sentiment dispersion |

## ④ Market consequences – "what else" to measure beyond stock price

| Dimension | Metric | Why clients care |
|---|---|---|
| Price | abnormal return (AR), cumulative AR (CAR) via event study | ✅ baseline implemented |
| Persistence | reversal vs. drift over +1…+20 days | separates real info from noise |
| Risk | realised & implied volatility, option skew | hedging, risk desks |
| Activity | abnormal volume, turnover | attention / disagreement |
| Liquidity | bid-ask spread, depth | execution cost |
| Credit | CDS spreads, bond yields | credit funds, treasurers |
| Contagion | spill-over to suppliers, customers, competitors, sector | ⏳ (named in playbooks as `peer_spillover`, not measured yet) |
| **Confidence / sentiment indices** | VIX, investor & consumer sentiment surveys, put/call ratios, fund flows | macro & market confidence |
| Analyst behaviour | estimate revisions, rating changes, forecast dispersion | sell-side & IR clients |
| Attention | search trends, social volume, news volume | early-warning |

## ⑤ Business & real-economy consequences (longer horizon)

Management responses (guidance changes, denials, buybacks), cost of capital,
capex/hiring decisions, customer churn & supplier terms, regulatory action,
reputation/ESG ratings. These close the loop: they confirm or refute the
original claims, which feeds back into ① reliability.

## Hypotheses to test first (good demo material)

1. **H1 – Reliability discount:** price reaction to a claim scales with its
   reliability score.
2. **H2 – Rumour reversal:** low-reliability news shows a positive short-term
   reaction followed by a reversal; high-reliability news does not reverse.
3. **H3 – Corroboration vs. echo:** independent corroboration increases
   impact; syndicated copies of the same story do not (beyond attention).
4. **H4 – Aspect matters:** supply-chain and regulation news propagate to
   related firms more than leadership news.
5. **H5 – Novelty:** rehashed news has near-zero abnormal return.

## Methodology guard-rails (credibility with finance clients)

* **Point-in-time only:** features use data available at `as_of` – no look-ahead.
* **Survivorship:** include delisted companies in backtests.
* **Multiple-testing:** pre-register hypotheses; out-of-sample periods.
* **Confounders:** control for earnings dates, market/sector moves, size, momentum.
* **Model versioning:** every score carries `model_version`; results are reproducible.
