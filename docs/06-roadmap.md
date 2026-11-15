# Roadmap (startup, demo-first)

| Phase | Goal | Done | Next | Cloud cost |
|---|---|---|---|---|
| **0 – Foundation** ✅ | Enterprise-shaped skeleton | One template for every module, boundaries enforced in CI, ADRs, cost guardrails, contracts (event schemas, OpenAPI) | – | $0 |
| **1 – Real data** | Real news and prices | 8 sources incl. per-company feeds for all 73 companies; EODHD prices (US + ASX); source track records from corroboration; opinion pieces filtered | A corroborating source: SEC filings (needs a contact email in requests), ASX announcements or a news wire (licensed); grow the labelled set to 200+ | $0 local + data licences |
| **2 – Smarter semantics** | Beat the word-list baseline | Economy LLM reading (0.96 event accuracy on the labelled set, about $0.06 per 1,000 sentences); AI briefs from our facts with safety checks | Stricter event-type and relevance checks for single-source items; supplier and peer links (spillover) | LLM tokens (capped at $5/month) |
| **3 – Evidence** | Prove the hypotheses on history | Track record per event type on the website | Backtests: which update moves which measure, rumour reversal, reliability vs reaction | $0–10 |
| **4 – Client demo** | Something a client can click | Website (watchlist, event pages, how it works), phone layout, Discord alerts | Accounts and sign-in (Cognito), email alerts (AWS SES), the Stage-2 AWS stack | ≈ $5–40/mo |
| **5 – Pilot** | 1–3 design partners | – | Multi-tenant, more alert channels, SLAs, onboarding | revenue-funded |

## Definition of done (every change)
`make check` passes (format, lint, types, architecture rules, tests,
contracts, website build) · docs/ADR updated if a decision changed · no
secrets in code or logs · every new file has a stated reason (its docstring).
