# NewsImpact

*by Inspiring Ming*: <https://github.com/Inspiring-Ming/NewsImpact>

NewsImpact turns financial news into checked storylines:

1. **Monitor** a curated set of US and Australian news outlets.
2. **Understand** what each article claims, about which company, and where the claim came from.
3. **Link** related news into a storyline, for example a misconduct report, then a resignation, then a successor.
4. **Anticipate** the decisions each stage typically triggers.
5. **Check** those expectations against independent evidence: other outlets, filings, and market data.
6. **Conclude**, with suggestions and full provenance.

Everything is used through an interactive website.

> Status: **Phase 0 – Foundation.** The demo runs offline at zero cost on fictional data. No AWS
> resources exist until you apply `infra/` yourself.

## Quick start

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # one-time: install uv (Python) - Node 22 is also needed
make install     # Python + website dependencies
make dev         # API on :8000 + website on http://localhost:5173  (demo profile: click "Load demo data")
make check       # format, lint, types, architecture rules, tests, contracts, website build
make docker      # production image (API + website) on http://localhost:8000
```

To watch the real outlets, copy `.env.example` to `.env` and set these values:
- `NI_PROFILE=live`
- `NI_STORE=sqlite`
- `NI_MONITOR_EVERY_MINUTES=15`
- optionally `NI_MARKET_DATA=eodhd` with `NI_EODHD_API_KEY`
- optionally `NI_LLM_PRESET=quality`

## The website

Who it is for: professional equity investors following a list of stocks (analysts, portfolio managers, serious self-directed investors); second, investor relations teams. What it tells them: **does anything I follow need attention, is it real (verified by independent sources, the company or a filing), has the market reacted, and what usually happens next?** See [ADR 0028](docs/adr/0028-primary-user-verified-events.md).

| Page | What it shows |
|---|---|
| **Watchlist** (home) | Views: ★ My companies (starred, kept in the browser) · Verified events (default) · All events (including unverified single-source signals) · All companies. Four key numbers for the view (click one for its detail), filters and sort, the impact map, and one compact table: Company (star, ticker, sector) · Latest event (linked to the original article) · What the news says · Stock vs market (provisional "so far" while the window is open) · Verified badge, sources, confidence. Opinion and feature pieces open no event. |
| **Event** (opens from a row) | Key numbers with visuals (stock vs market, trading volume vs normal, news confidence, reactions as expected), then three tabs: **Overview** (price chart with each update marked; "Watch next" and "What research shows", with its published source) · **Updates** (a timeline: date axis, gaps between updates, tone, rumour, sources, confidence and the stock's reaction per update) · **Expected vs actual** (one section per measure, defined on the page; each update's measured bar against the stock's normal range, the expectation and the result in words; the method and exact versions at the bottom). |
| **How it works** | Three tabs of live data: 1. News sources (reliability, how often each covers our companies and leads to an event), 2. Events we detect (usual updates, time window, measured gaps, reading accuracy), 3. Does it move the stock? (per event type: expected share price direction, average measured move, unusual moves, how often it moved as expected). Definitions on hover. |

Event types: Leadership change, Product safety, Takeover, Earnings beat, Earnings miss, Cyber incident, Job cuts, Supply disruption. Each event is a chain of dated **updates** (e.g. Leader under pressure → Leader steps down → New leader named).

The plain-English answers are written once by the API (`/v1/companies`, `/v1/events/{id}/summary`), so the website and any integration use the same words. Names come from the data files: company names, countries and GICS sectors from `entities.json`, event and update titles from `playbooks.json`, source names from `sources.json`.

## How it works: seven modules, in the order news flows

```
 monitor ▶ ① sources ─▶ ② semantics ─▶ ③ reliability ─┬─▶ ④ storylines (chain of events → decisions)
           outlets &     claims, event   outlet &      └─▶ ⑤ impact     (who is affected, how much)
           articles      types, origins  claim trust             │
              ▲                                                  │
              └────── search listed outlets for the next stage ◀─┤
                                                                 ▼
           ⑥ market (price, volume, volatility; NYSE/Nasdaq or ASX) ─▶ ⑦ validation ─▶ conclusion
```

## Repository map

```
src/newsimpact/
  sources/ semantics/ reliability/ storylines/ impact/ market/ validation/   business modules
  llm/            budgeted, cached gateway to local or hosted LLMs (optional)
      __init__.py   module card: purpose, how to extend, publishes / consumes
      models.py     its data + events (the only file other modules may import)
      logic.py      pure math and rules, where there are any
      ports.py      interfaces it needs from the outside world
      service.py    the workflow: events in → logic + ports → events out
      adapters/     one file per technology (rss.py, eodhd.py, sqlite.py, ollama.py…)
  shared/         event base classes, event bus, text ids, SQLite helper (adapters only)
  app/            settings, wiring (picks technologies), API + website, queries, monitoring
web/              the website (React + TypeScript): src/features/<page>/, src/shared/, routes.tsx
data/reference/   REAL curated data, each value with its reason: outlets, companies (US + ASX),
                  taxonomy, playbooks, methodology (windows, thresholds), LLM presets & prices
data/demo/        FICTIONAL demo data in the same formats
data/eval/        hand-labelled sentences: the quality gate for any analysis chain
tests/            mirrors src/; tests/e2e runs the real wiring
schemas/events/   generated JSON Schemas of every event
scripts/          contract exports (event schemas, OpenAPI)
infra/terraform/  AWS cost guardrails (apply manually)
docs/             vision, requirements, architecture, research, AWS cost, roadmap, settings, ADRs
```

**Common changes that need no code:**
- **Watch another outlet:** add a row to `data/reference/sources.json`.
- **Watch another company:** add an alias to `data/reference/entities.json`; ASX tickers end in `.AX`.
- **Detect a new kind of event:** edit `data/reference/taxonomy.json`.

Why each outlet, window and threshold was chosen:
[docs/07-coverage-and-settings.md](docs/07-coverage-and-settings.md).
How to extend everything else: [docs/03-architecture.md](docs/03-architecture.md).

© Inspiring Ming. All rights reserved.
