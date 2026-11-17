# Documentation

| Doc | Purpose |
|---|---|
| [01-vision-and-scope](01-vision-and-scope.md) | Problem, product, target clients, data licensing |
| [02-non-functional-requirements](02-non-functional-requirements.md) | Measurable quality targets + standards we align with |
| [03-architecture](03-architecture.md) | The modules, repository map (why every folder exists), module template, enforced rules, how to extend, reproducibility, frontend, scaling |
| [04-research-framework](04-research-framework.md) | Outlet reliability → content layers → storylines → validation → human decision → market → business; hypotheses |
| [05-aws-cost-plan](05-aws-cost-plan.md) | Account hardening, staged AWS design, cost traps |
| [06-roadmap](06-roadmap.md) | Phases from foundation to client pilot |
| [07-coverage-and-settings](07-coverage-and-settings.md) | What we monitor, for how long, and the reason for every number |
| [08-codebase-guide](08-codebase-guide.md) | Every folder and file, how they connect (the hourly round, a page request), and recipes to add, change or remove a part |
| [adr/](adr/) | Architecture Decision Records (why we chose what we chose) |

Docs live with the code and change in the same pull request as the code.

## Architecture Decision Records

Why we chose what we chose. ADRs are historical records: a later one supersedes an
earlier one rather than editing it. New ones start from [adr/0000-template.md](adr/0000-template.md).

| ADR | Decision |
|---|---|
| [0001](adr/0001-modular-monolith-hexagonal.md) | Modular monolith with hexagonal architecture |
| [0002](adr/0002-python-uv-tooling.md) | Python 3.12 with uv, ruff, mypy (strict), pytest |
| [0003](adr/0003-event-contracts-cloudevents.md) | Event contracts: CloudEvents envelope + versioned JSON Schemas |
| [0004](adr/0004-aws-serverless-cost-first.md) | AWS, serverless and scale-to-zero first |
| [0005](adr/0005-llm-provider-agnostic.md) | LLM access through a provider-agnostic port |
| [0006](adr/0006-point-in-time-data.md) | Point-in-time, versioned data |
| [0007](adr/0007-reliability-bayesian-model.md) | Bayesian (Beta-Binomial) source reliability as baseline |
| [0008](adr/0008-package-by-capability.md) | Package by business capability, not by technical layer |
| [0009](adr/0009-frontend-api-first.md) | API-first web frontend (React + TypeScript SPA, OIDC) |
| [0010](adr/0010-storylines-and-follow-up-discovery.md) | Storylines with playbooks, and automatic follow-up discovery |
| [0011](adr/0011-curated-source-registry.md) | Start with a curated list of outlets; grow it by configuration |
| [0012](adr/0012-uniform-module-template.md) | One file template for every module; data lives with its module |
| [0013](adr/0013-taxonomy-and-analysis-chain.md) | Semantics: taxonomy as data, analysis as a chain of steps |
| [0014](adr/0014-validation-with-independent-evidence.md) | Validate storylines with independent evidence before concluding |
| [0015](adr/0015-monitoring-and-local-persistence.md) | Automatic monitoring with SQLite persistence (Postgres later) |
| [0016](adr/0016-settings-from-reasons.md) | Every setting is a reasoned prior, measured and revised |
| [0017](adr/0017-attribution-copies-independent-origins.md) | Count independent origins, not outlets: attribution and copy detection |
| [0018](adr/0018-llm-gateway-local-or-hosted.md) | One LLM gateway: local or hosted, budgeted, cached, evaluated |
| [0019](adr/0019-market-evidence-automation.md) | Automated, reproducible market evidence |
| [0020](adr/0020-website-replaces-cli.md) | An interactive website replaces the command line |
| [0021](adr/0021-eodhd-multi-exchange.md) | EODHD for prices; each stock measured on its home exchange |
| [0022](adr/0022-website-briefing-first.md) | Website: briefing first, two pages, built to grow |
| [0023](adr/0023-company-watchlist-plain-answers.md) | Company watchlist with plain answers (supersedes the layout in 0022) |
| [0024](adr/0024-watchlist-table-and-event-tabs.md) | Watchlist table, event tabs and more event types (supersedes the layout in 0023) |
| [0025](adr/0025-confidence-from-independent-sources.md) | Confidence from independent sources, company news feeds, definitions on hover |
| [0026](adr/0026-impact-map-and-news-signals.md) | Impact map, "what the news says", plain method results |
| [0027](adr/0027-track-record-and-cited-guidance.md) | Source track records, cited guidance, visual cells |
| [0028](adr/0028-primary-user-verified-events.md) | Primary user, verified events vs unverified signals |
| [0029](adr/0029-alerts-module.md) | Alerts for followed companies (Discord first) |
| [0030](adr/0030-guidance-priority-and-briefs.md) | What we tell the user: priority, what to check, three-line briefs |
| [0031](adr/0031-project-review-structure.md) | Project review: one place per concern, nothing unused |
| [0032](adr/0032-users-and-ci.md) | Multi-user ready (local sign-in first), CI per kind of risk |
| [0033](adr/0033-assistant-tools-and-mcp.md) | AI assistant: read-only tools over our data, on the website and over MCP |
| [0034](adr/0034-expectations-per-case-and-chance.md) | Share price expectations per case, judged against chance; How it works explains every number |
| [0035](adr/0035-legal-and-capital-return-events.md) | Two more event types: Legal & regulatory, Dividends & buybacks |
| [0036](adr/0036-companies-followed-from-the-news.md) | Which companies we follow: decided from the live news, within the S&P 500 and ASX 200 |
