# NewsImpact

*by Inspiring Ming*: <https://github.com/Inspiring-Ming/NewsImpact>

NewsImpact reads financial news about 73 large US and Australian companies, spots
market-moving events (a CEO leaving, a takeover, an earnings miss...), checks how
well each one is sourced, and measures how the stock reacted against its market.

**For** professional equity investors who follow a list of stocks (and investor
relations teams). **It answers:** does anything I follow need attention, is it
real, has the market reacted, and what usually happens next?
It states facts and what to check, never what to buy or sell.

## The website

| Page | What it shows |
|---|---|
| **Watchlist** (home) | Key numbers (click for detail); two tabs: **All** and **Priorities** (a board of what to act on and check); an impact map of stock moves by sector; every company with an event: priority, the news, the stock vs its market, and its sources (confirmed or not). Star (★) companies to follow them. |
| **Event** | A three-line brief, what to check now, the price chart, a timeline of updates, and expected vs actual market reactions. |
| **How it works** | Whether the news reaches every company, the news sources and their track records, the event types, and whether each type really moves stocks. |

Every underlined word explains itself on hover. Followed companies can get
**Discord alerts** when something changes.

## Run it

```bash
make install     # Python (uv) + website (Node 22) dependencies
make dev         # demo on fictional data: API :8000 + website http://localhost:5173
make check       # everything CI runs: format, lint, types, architecture rules, tests, contracts, build
```

For live news, copy `.env.example` to `.env` (git-ignored, keys stay there) and set:

| Setting | What it does |
|---|---|
| `NI_PROFILE=live`, `NI_STORE=sqlite`, `NI_MONITOR_EVERY_MINUTES=60` | read the real sources every hour and keep state |
| `NI_MARKET_DATA=eodhd` + `NI_EODHD_API_KEY` | stock prices (US and ASX) |
| `NI_LLM_PRESET=economy` + `ANTHROPIC_API_KEY` | AI reading and briefs; capped by `NI_LLM_MONTHLY_BUDGET_USD` (default $5) |
| `NI_DISCORD_WEBHOOK_URL` | alerts for followed companies |
| `NI_AUTH=local` (default) | one built-in admin, no sign-in: for one person on their own computer. Many users: Amazon Cognito (next step) |

Then `make docker` serves the site on <http://localhost:8000>.

## How it works

```
every hour ▶ sources ─▶ semantics ─▶ reliability ─▶ storylines ─┐
             news         what is       how far to     news joined  │
             articles     claimed       trust it       into events  ▼
                                              market (price, volume) ─▶ validation
                                                                         │ confirmed? as expected?
                         app/views: priority, what to check, briefs ◀────┘
                                    │                     │
                                 website / API         alerts (Discord)
```

Each step is a module with the same five files, so every module reads the same
way. Modules only talk through events and each other's data classes; CI enforces it.

## Repository map

```
src/newsimpact/
  sources/ semantics/ reliability/ storylines/ market/ validation/   the pipeline
  alerts/       tell each follower what changed (Discord now, email later)
  identity/     who is signed in and what they may do (local now, Cognito next)
  llm/          one budgeted, cached gateway to language models
     every module: __init__.py (what it is) · models.py · logic.py · ports.py · service.py · adapters/
  shared/       event base classes, event bus, text ids, SQLite helper
  app/          settings · wiring/ (plugins.py: every technology by name) · api/ (one router
                per area) · monitor.py (the hourly round, step by step) · views/ (what the site shows)
web/src/        the website: features/<page>/, shared/ (labels, badges, charts), routes.tsx
data/reference/ the real curated data, each value with its reason (sources, companies,
                event types, playbooks, thresholds, model prices)
data/demo/      fictional data in the same formats   data/eval/  hand-labelled sentences
tests/          mirrors src/ (tests/app for the API and views, tests/e2e for the full pipeline)
schemas/        generated event schemas   scripts/  their export   docs/  design and decisions
```

## Change it

| I want to... | Do this |
|---|---|
| read another news source | add a row to `data/reference/sources.json` |
| follow another company | add it to `data/reference/entities.json` (ASX tickers end in `.AX`) |
| detect another kind of event | `taxonomy.json` (words) + `playbooks.json` (its updates, expected reactions, research) |
| use another technology (price vendor, storage, AI provider, alert channel) | its adapter in the owning module + one entry in `app/wiring/plugins.py` |
| add API endpoints | `app/api/routes/<feature>.py` + one entry in `ROUTES` |
| add a step to the hourly round | one function + one line in `ROUND` (`app/monitor.py`) |
| add a website page | a folder in `web/src/features/`, one line in `routes.tsx` |

Each change has one test folder to match (tests mirror the code). Moving a step to
the cloud or a module to another language is a plug-in, not a rewrite.
What every folder and file does and how they connect: [docs/08-codebase-guide.md](docs/08-codebase-guide.md).
Everything else, with the reasons behind the design: [docs/03-architecture.md](docs/03-architecture.md).
Why every source, window and threshold was chosen: [docs/07-coverage-and-settings.md](docs/07-coverage-and-settings.md).

© Inspiring Ming. All rights reserved.
