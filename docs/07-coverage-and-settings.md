# Coverage and settings: what we monitor, for how long, and why each number

**Rule:** no number is arbitrary. Each setting starts as a **prior**: a value
with a written reason taken from the literature, industry practice or stated
judgement. It is then **measured** on our own data on the website's
How it works tabs, and **revised** through a versioned file change. Each assessment
records the hash of the files it used (`provenance`), so a result can always
be traced back to the exact settings that produced it.

| Where | What | Measured by |
|---|---|---|
| `data/reference/sources.json` | which outlets | How it works → News sources (reliability, track record, coverage) |
| `data/reference/entities.json` | which companies (US + ASX) | How it works → News sources ("About our companies") |
| `data/reference/taxonomy.json` | which events, attribution and background wording | How it works → Events we detect; accuracy on the labelled set: `GET /v1/evaluation` |
| `data/reference/playbooks.json` | event updates, expected reactions, time windows, research findings | How it works → Events we detect, Does it move the stock? |
| `data/reference/methodology.json` | measurement windows, significance, thresholds for conclusions and copies, exchanges (sessions, benchmarks) | How it works → Does it move the stock? |
| `data/reference/llm_models.json` | LLM presets (with reasons) and prices (dated, with source) | the spend ledger (`/v1/overview`) |
| environment (`NI_*`) | deployment only: storage, providers, budget | – |

## 1. What to monitor

### Companies (the universe)
**Prior:** about 20 of the largest, most-covered US companies (`entities.json`).

- **Coverage is concentrated:** media coverage clusters on large firms (Fang & Peress 2009), so the story chains we want to show actually occur there.
- **Prices are clean to measure:** liquid stocks absorb news quickly, so event-study measurements are less noisy.
- **Clients follow them:** they are the names prospective clients watch.

**Measure:** `coverage` shows, per outlet, the share of articles that name a watched company.

**Revise:** go deep on one sector rather than broad across many. A sector benchmark ETF and supplier/peer links make the impact and validation steps much stronger.

**Australia.** The same rules apply to the ASX:
- **Companies:** about 15 of the largest, most-covered ASX names (BHP, CBA, CSL, the major banks, Telstra, Woodside, Qantas and others), plus Atlassian, an Australian company listed in the US.
- **Measurement:** ASX tickers end in `.AX`. They are measured on Sydney's trading session against the ASX 200 ETF (STW), because a stock reacts on its home exchange.
- **News published overnight:** US-hours news reaches the ASX on the next Sydney session.

### Outlets (the sources)
The prior list uses four criteria, in order:

1. **Origins first.** Wires, regulatory filings and company press releases are where news starts; most outlets re-report them. An origin adds independent evidence, and a copy does not.
2. **Reach among investors.** Major business desks (BBC, Guardian, NYT, CNBC, MarketWatch) shape attention, which drives reactions (Da, Engelberg & Gao 2011 show attention moves prices).
3. **Machine-readable and allowed.** A public feed whose terms permit our use. Showing content to clients needs each publisher's licence.
4. **Earns its place.** Judged on our own data (website → How it works → News sources):

| Column | Meaning | Keep if… |
|---|---|---|
| company | share of articles naming a watched company | meaningfully above 0 |
| trigger | share containing a storyline trigger | above 0 over 30 days |
| copies | share that copy another outlet | low (a high value means re-reporting, little new evidence) |
| first | storyline stages this outlet reported first | > 0 (an origin) |

**Decision rule after 30 days of monitoring:**
- **Disable** outlets with ~0% company share and 0 stages.
- **Look for better feeds** for outlets that copy heavily: a company-specific feed, or the original wire.
- **Add** an outlet when follow-up search keeps finding stages first reported by an unlisted one. Trial it with `NI_ACCEPT_UNLISTED_SOURCES=true`, then list it.

Company news feeds (added 2026-11-15):
- **Yahoo Finance per-company feeds:** one feed per tracked company (US symbols and ASX symbols such as `BHP.AX`), about 20 recent items each. General business sections only mention a few of our companies; per-company feeds give every followed company its own news stream, and each round a rotating slice of the other index members is read too, so any of them can qualify (methodology.json "following", ADR 0036). Items mix Yahoo's own reporting with syndicated pieces (Motley Fool, Investing.com), so the source type is **aggregator**, starting at 67% reliability, below a newspaper's 75%. Cost measured on the first round: about 1,000 new articles analysed for about $0.012 with the economy model. Free for personal and research use; check Yahoo's terms before showing content to paying clients.

Australian outlets on the list:
- **ABC News Business** and **The Sydney Morning Herald Business:** free feeds, checked 2026-11-15.
- **ASX company announcements:** listed but disabled. They are the authoritative source for ASX companies (like SEC filings in the US), but have no free feed; enable them through a licensed announcements feed.
- **AFR and The Australian:** their feeds are not openly available (they returned 403 or 404).

*Example, first live round (2026-11-15):* PR Newswire's and MarketWatch's general feeds had 0% of articles naming a watched company. NYT had 42%. Under the rule, PR Newswire should move to company-specific feeds rather than the all-releases feed.

This follows how commercial news-analytics products work: premium wires plus selected web sources, scored per company for relevance and novelty (e.g. RavenPack's relevance and novelty scores). We start with a smaller list and measure it.

### Topics (what counts as an event)
**Prior:** event types documented to move prices:
- earnings and guidance
- M&A
- leadership changes
- regulatory and legal action
- product recalls
- supply disruptions
- cyber incidents (data breaches, outages)
- job cuts
- dividends and buybacks

All nine are covered by playbooks (taxonomy-v9). Until 2026-11-17 a regulator action or lawsuit only continued a product safety or cyber event; a check of 2,752 stored articles found 41 such articles about 13 of our companies (Intel shareholder suits, Meta's Italy fine, Nvidia DOJ probes, ASIC suing CBA) and 11 dividend or buyback articles about 7 (Costco, ExxonMobil) that opened no event, so both became event types (ADR 0035). Checked and not added: analyst rating changes (16 articles, mostly opinions or about another company), drug approvals (3), capital raisings, credit ratings, index changes and strikes (0–1 each). Each company also carries its GICS sector in `entities.json`, the standard industry classification financial users filter by.

Firm-specific news that can be *identified* as a known event type explains far more stock volatility than unidentified news (Boudoukh, Feldman, Kogan & Richardson 2019). Other sentences are stored but do not open storylines.

**Measure:** `evaluate` reports precision and recall per event type on the labelled set.

**Revise:** add types in `taxonomy.json` (bump its version); every playbook trigger must exist there (checked at start-up).

## 2. How long a story is followed

Each playbook has a **link window**:

- **What it does:** a new report within that many days of the latest stage belongs to the same story, and follow-up search keeps looking for that long.
- **When monitoring stops:** a resolved story stops follow-up search but still absorbs late reports of stages it already has. A story with no new stage within its window goes dormant.

| Playbook | Window | Reason (prior) |
|---|---|---|
| leadership_crisis | 60 days | Interim leaders are named at or soon after a departure; a permanent search can take months. 60 days captures the interim or announced successor without merging unrelated leadership news. |
| product_safety | 90 days | Probes and lawsuits follow a recall by weeks to months. |
| m_and_a | 90 days | Rumours that become deals are typically confirmed within about a quarter; after that the rumour is treated as faded. |
| results | 30 days | Forecast revisions and guidance updates land within weeks of a results release, inside one reporting cycle. One event per release, read as better, worse or mixed. |
| cyber_incident | 90 days | Regulator inquiries and class actions typically follow a breach disclosure by weeks to months. |
| job_cuts | 30 days | Details (numbers, sites, costs) usually emerge within weeks of the first report. |
| supply_disruption | 60 days | Supply problems tend to resolve or escalate (lost sales, guidance cuts) over one to two months. |
| legal_regulatory | 180 days | Probes and lawsuits take months to settle or be decided, and follow-on suits arrive in waves; one case, its copycat suits and its outcome stay one story. |
| capital_return | 30 days | Details (amount, dates, funding) follow within weeks; the next payout decision comes with the next results. |

**Calibration rule** (`methodology.json` → validation):
- **Formula:** once a playbook has ≥ 20 observed gaps between stages, the suggested window is the **90th percentile of observed gaps × 1.25**.
- **Why the 90th percentile:** it covers most real cases.
- **Why the 25% margin:** small samples underestimate the tail, and a slightly long window costs little.
- **Where to see it:** How it works → Events we detect shows the measured gap next to the window; adopting a suggestion is a one-line change in `playbooks.json`.

### Realistic timelines: when stages follow within days
Real stories can move much faster than a playbook's window. In the Nvidia case reported by our outlets, a report about the CEO's personal conduct was followed by his resignation within a week, and an interim CEO the same day. The setup handles this in four ways:

- **A pressure stage.** "public pressure" covers a misconduct report or an apology (event types `leadership_misconduct`, `leadership_apology`). A story can also start directly at the departure.
- **One story.** The link window (60 days) is an upper bound, not an expected duration. Fast sequences stay in one storyline.
- **Overlapping stages.** Stages closer than the longest measurement window (4 trading days, `overlap_trading_days`) share trading days, so their separate reactions cannot be told apart. The assessment marks them "overlaps previous stage".
- **Out-of-order reporting.** Outlets publish events in a different order than they happen. In the live data, BBC's "CFO in charge for now" came out before the resignation story. A resolved story therefore still absorbs reports of its earlier stages published within **3 days** (`late_report_days` in `playbooks.json`) and is not reopened.
- **One combined reaction.** It then also reports a single reaction measured from the first to the last of those close stages. That combined number is the realistic one to read for a fast-moving story.

## 3. How market reactions are measured

All values are in `methodology.json` → market, each with its reason.

| Setting | Value | Reason |
|---|---|---|
| Estimation window | 120 trading days | Within the 120–250-day range common in event studies (MacKinlay 1997): stable beta, current business |
| Gap before event | 10 trading days | Keeps pre-event leakage out of "normal" behaviour |
| Price window | day 0 to +1 | Most of the price response to firm news happens within a day or two |
| Volume window | day 0 to +2 | Trading stays elevated slightly longer than prices |
| Volatility window | day 0 to +4 | Uncertainty settles more slowly; a variance needs a few days |
| Significance | \|z\| ≥ 1.96 | Two-sided 5% test |
| Trading session | 16:00 close of the home exchange (New York or Sydney) | After-close news can only be traded on the next session |
| Benchmarks | SPY (US), STW (ASX 200) | Each stock is compared with its own market; use a sector ETF when focusing on one sector |

**Across many events**, `calibrate` runs the standardized cross-sectional (BMP) test (Boehmer, Musumeci & Poulsen 1991) per stage and channel:
- **Why this test:** it stays valid when news itself raises volatility.
- **Fewer than 20 events:** results are labelled *indicative*. Brown & Warner (1985) evaluate tests on samples of 50; below about 20, one outlier dominates the average.
- **What the findings do:** "supported" or "contradicted" replace playbook priors with measured facts.

### Price source: EODHD
**Chosen:** EODHD end-of-day data (`NI_MARKET_DATA=eodhd`).

**Why:**
- **Both markets, one subscription.** It covers US and ASX listings with split- and dividend-adjusted prices.
- **Australian rights.** It states it is an official ASX data provider with exchange redistribution rights on its plans.
- **Cost.**
  - The end-of-day "All World" plan is listed at about **$19.99/month**; confirm the current price on EODHD's pricing page.
  - A free tier (20 calls/day, personal use only) is enough for development. With the local price cache, each company is fetched about once a day.

**Before showing results to clients:** EODHD requires a commercial licence for products. Commercial pricing is separate and was not checked here.

**Rejected alternatives:**
- **Stooq:** blocks scripted access.
- **Unofficial Yahoo scrapers:** not licensed.
- **US-only vendors:** do not cover the ASX.
- **Alpha Vantage and FMP:** their free tiers are non-commercial, and their global coverage costs more.

**Reproducibility without the API:** `NI_MARKET_DATA=csv` reads vendor exports.

## 4. When a claim counts as confirmed

`methodology.json` → validation and sources:

| Setting | Value | Reason |
|---|---|---|
| Copy threshold | ≥ 80% shared 5-word shingles | Shingle resemblance (Broder 1997); catches syndication and light rewrites |
| Copy window | 3 days | Copies of wire stories appear within hours to days |
| Copy novelty | 0.2 | Reprinted news is not new information; investors over-react to stale news and then reverse (Tetlock 2011) |
| Corroborated | 2 independent origins | Classic two-source journalistic standard |
| Confirmed | 3 origins, or a filing or company statement | A coordinated error across three origins is unlikely; the company or regulator is authoritative |
| High confidence | market confirms ≥ 60% of measured expectations | A clear majority |

**Independent origin** means the outlet itself, a cited outlet ("…, Reuters reported"), the company, a filing, or the outlet that a copy came from. Ten outlets repeating one scoop count as **one** origin.

## 5. LLM cost settings

**Defaults:** LLM off (`NI_LLM_PRESET=off`). Two hosted presets plus a local one, each with its reason in `llm_models.json`: **quality** = Claude Opus 5.5 (the default when you switch Claude on), **economy** = Claude Haiku 5.5, **local** = an Ollama model. When on:
- a monthly cap of **$5** (`NI_LLM_MONTHLY_BUDGET_USD`)
- **200 calls** per monitoring round
- only **candidate** claims are sent (where the free baseline already saw an event, attribution, speculation or background)

Above a limit, the free result is kept. **Measured on 2026-11-15** against the labelled set (52 sentences), with every sentence sent to the model (`NI_LLM_SCOPE=all`). Cost is the real spend from the ledger:

| Analysis | Event type | Attribution | Rumour | Background | Per 1,000 sentences |
|---|---|---|---|---|---|
| Word lists (free) | 0.69 | 0.96 | 0.96 | 0.98 | $0 |
| **economy** (Claude Haiku 5.5) | 0.96 | 0.98 | 1.00 | 0.96 | **≈ $0.06** |
| quality (Claude Opus 5.5) | 0.98 | 0.89 | 0.92 | 0.98 | ≈ $2 |

**Choice: `economy` with scope `all`.** It is nearly as accurate as `quality` for about 1/35 of the cost. At today's volume that comes to cents per month, far below the $5 cap.

Why scope `all` rather than `candidates`: the candidates filter only sends sentences where the word lists already saw something. The paraphrases that the word lists miss ("hand over the CEO role", "pulled from pharmacies") therefore never reached the model. That held `economy` to 0.85 on event type.

**Re-measured on 2026-11-16 (56 sentences)** after the subject check (classifier v2: the model also names the company the event happens to, and says that share-price comparisons, previews, forecasts, partnerships and licensing deals are not events): event type 0.95 (v1 on the same set and day: 0.93), attribution 0.93 (v1: 0.93), rumour 1.00 (v1: 0.98), background 0.96 (v1: 0.96). No loss on the labelled set, and on the live feed it removed events that belonged to another company or were not events at all. Example: Cerebras's results had been shown as a Microsoft earnings beat because Microsoft was mentioned.

With only 56 sentences, a difference of one or two sentences is noise. Re-measure with `GET /v1/evaluation` when the labelled set grows to 200–500 real sentences.

## 6. Changing a number

1. **Edit the value and its reason** in the reference file, and bump the file's `version`.
2. **Run the checks:** `make check`; `GET /v1/evaluation` for semantics changes; `GET /v1/calibration` for windows and thresholds.
3. **Write an ADR** if the rule itself changes, not just the value.
4. **Trace it later:** new assessments carry the new file hash, so before and after are always distinguishable.

## References
- Boehmer, Musumeci & Poulsen (1991), *Event-study methodology under conditions of event-induced variance*, JFE.
- Boudoukh, Feldman, Kogan & Richardson (2019), *Information, trading, and volatility: evidence from firm-specific news*, RFS.
- Broder (1997), *On the resemblance and containment of documents*.
- Brown & Warner (1985), *Using daily stock returns: the case of event studies*, JFE.
- Da, Engelberg & Gao (2011), *In search of attention*, JF.
- Fang & Peress (2009), *Media coverage and the cross-section of stock returns*, JF.
- MacKinlay (1997), *Event studies in economics and finance*, JEL.
- Tetlock (2011), *All the news that's fit to reprint: do investors react to stale information?*, RFS.
