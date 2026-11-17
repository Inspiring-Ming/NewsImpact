# NewsImpact

*by Inspiring Ming*: <https://github.com/Inspiring-Ming/NewsImpact>

NewsImpact reads financial news about the S&P 500 and ASX 200 companies, follows the ones
the news is about (up to 150 at a time, decided from the live news), spots
market-moving events (a CEO leaving, a takeover, an earnings miss...), checks how
well each one is sourced, and measures how the stock reacted against its market.

**For** professional equity investors who follow a list of stocks (and investor
relations teams). **It answers:** does anything I follow need attention, is it
real, has the market reacted, and what usually happens next?
It states facts and what to check, never what to buy or sell.

## The website

| Page | What it shows |
|---|---|
| **Watchlist** (home) | Two views: **All events** and **★ My companies**. Key numbers (click for detail); two tabs: **All** (an impact map of stock moves by sector, then a feed of every company with an event: priority, the news, the stock vs its market, and its sources, confirmed or not) and **Priorities** (a board of what to act on and check). Star (★) companies to follow them. |
| **Event** | Three tabs: **Overview** (a three-line brief, what to check now, the price chart, this type's track record), **Updates** (a timeline) and **Expected vs actual** (market reactions). |
| **How it works** | Three tabs: **News sources** (how far we trust each, from its track record), **Events we detect** (from sentence to confirmed event, and how far our events went) and **Does it move the stock?** (each case against research and chance). All settings with their reasons sit below. |
| **Ask NewsImpact** (button on every page) | A chat assistant: questions answered by AI from our own data only, checked, with the links it used. On an event page it knows the event; suggested questions come from live data. |

A ticker under the header shows the latest events. Every underlined word explains
itself on hover. Starred companies can get **Discord alerts** when something changes.
AI assistants (Claude Desktop, Claude Code...) can query the same data through our **MCP server** (`make mcp`).

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
| `NI_DISCORD_WEBHOOK_URL` | alerts for starred companies |
| `NI_AUTH=local` (default) | one built-in admin, no sign-in: for one person on their own computer. Many users: Amazon Cognito (next step) |

Then `make docker` serves the site on <http://localhost:8000>.

### Put it online as a demo
Set in `.env` on the server: `NI_PROFILE=live`, `NI_STORE=sqlite`, `NI_AUTH=demo` and
`NI_ADMIN_TOKEN` (24+ random characters, never committed). Visitors then read every page
and may ask the assistant (20 questions a day shared by all); stars stay in their browser.
Only requests carrying `Authorization: Bearer <NI_ADMIN_TOKEN>` run updates or change the
followed companies. Run **one** instance (it runs the hourly round itself on one SQLite
file); see [ADR 0037](docs/adr/0037-hosting-a-public-demo.md) for what else to check
(feed terms, the host's rate limits).

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

Each hour also decides which companies we follow: an index member is followed once
3 articles name it within 7 days (`app/following.py`, `methodology.json` "following").
Only followed companies get their own news feed and have their sentences read by AI;
30 others are checked each round, in turn, so any of them can qualify.

Each step is a module with the same five files, so every module reads the same
way. Modules only talk through events and each other's data classes; CI enforces it.

## Repository map

```
src/newsimpact/
  sources/ semantics/ reliability/ storylines/ market/ validation/   the pipeline
  alerts/       tell each follower what changed (Discord now, email later)
  identity/     who is signed in and what they may do (local now, Cognito next)
  assistant/    answers questions from our data with read-only tools (website "Ask NewsImpact" + MCP)
  llm/          one budgeted, cached gateway to language models
     every module: __init__.py (what it is) · models.py · logic.py · ports.py · service.py · adapters/
  shared/       event base classes, event bus, text ids, SQLite helper
  app/          settings · wiring/ (plugins.py: every technology by name) · api/ (one router
                per area) · monitor.py (the hourly round, step by step) · following.py (which
                companies we follow) · views/ (what the site shows) · mcp.py (MCP server)
web/src/        the website: features/<page>/, shared/ (labels, badges, charts, assistant), routes.tsx
data/reference/ the real curated data, each value with its reason (sources, index members,
                company names, event types, playbooks, thresholds, model prices)
data/demo/      fictional data in the same formats   data/eval/  hand-labelled sentences
tests/          mirrors src/ (tests/app for the API and views, tests/e2e for the full pipeline)
schemas/        generated event schemas   scripts/  their export, index lists   docs/  design and decisions
```

## Change it

| I want to... | Do this |
|---|---|
| read another news source | add a row to `data/reference/sources.json` |
| follow a company now | star it (★) on the website: a starred company is always followed |
| add a company outside the indexes | add it to `data/reference/entities.json` with a `why` (ASX tickers end in `.AX`) |
| fix how the news writes a name | its entry in `entities.json`: `aliases`; `exact_case_aliases` for a name that is also a word ("Apple"); an index name never to match alone goes in `ambiguous_names` |
| refresh the index lists (quarterly) | `make universe` (runs `scripts/refresh_universe.py`, rewrites `universe.json`) |
| detect another kind of event | `taxonomy.json` (words) + `playbooks.json` (its updates, expected reactions per case, research) |
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
