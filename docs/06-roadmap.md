# Roadmap (startup, demo-first)

| Phase | Goal | Deliverables | Cloud cost |
|---|---|---|---|
| **0 – Foundation** ✅ | Enterprise-shaped skeleton | One template for every module, boundaries enforced in CI; **automatic monitoring of 6 live outlets** with SQLite state; taxonomy-driven analysis chain; reliability; storylines with multi-outlet corroboration; **validation against independent evidence → conclusions + suggestions** with provenance; CI; ADRs; cost guardrails | $0 |
| **1 – Real data** | Real news & prices for one sector | **EODHD key** (US + ASX adapter ready; commercial licence before client use); 30 days of monitoring → act on `coverage` (e.g. company-specific press-release feeds); EDGAR enabled; grow the labelled set to 200–500; resolved claims feed outlet reliability; supplier links; Postgres adapters | $0 local + data licence |
| **2 – Smarter semantics** | Beat the lexicon baseline | LLM `ClaimExtractor`/`ClaimStep` driven by `taxonomy.json`; labelled evaluation set (200–500 claims, incl. event types); embedding-based storyline linking; fix background-sentence false triggers | LLM tokens (capped) |
| **3 – Evidence** | Prove the hypotheses on history | Backtests: reliability vs. reaction, rumour reversal, **which storyline stage moves which channel** – becomes the sales deck | $0–10 |
| **4 – Client demo** | Something a client can click | Website ✅ (overview, storylines with price chart and evidence, outlets, calibration, quality, method); next: Cognito sign-in, Stage-2 AWS stack | ≈ $5–40/mo |
| **5 – Pilot** | 1–3 design partners | Multi-tenant, `notifications` capability (webhooks, Slack/Teams), SLAs, onboarding docs | revenue-funded |

## Definition of done (every change)
`make check` passes (format, lint, types, architecture rules, tests,
schemas) · docs/ADR updated if a decision changed · no secrets in code ·
every new file has a stated reason (module docstring).
