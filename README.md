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

What it tells a visitor: **when news about a company turns into a developing story, is it confirmed, and how did the stock react?**

| Page | What it shows |
|---|---|
| **Companies** (home) | Every company we follow (US and Australia). **Developing stories** first: each card shows the latest headline, the story so far as dated events, and four plain answers — status, stock reaction against its index (S&P 500 or ASX 200), whether the news is confirmed, and the strength of the evidence. **Waiting for confirmation** lists possible stories from a single outlet. **Also in the news** gives the latest headline per company, and **No recent news** lists the rest. |
| **Story** (opens from a card) | In short · What happened · How the stock reacted · Who was expected to react, and did they? · For analysts (statistics). |
| **How it works** | Four tabs named after the industry or research method each follows: News sources (source credibility), Story tracking (event detection), Expected reactions (behavioural finance), Market reaction check (event study). Each tab gives what we do, the rule with its real numbers, and the live evidence. |

The plain-English answers are written once by the API (`/v1/companies`), so the website and any integration use the same words. Names come from the data files: company names and countries from `entities.json`, story and event titles from `playbooks.json`, outlet names from `sources.json`.

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
