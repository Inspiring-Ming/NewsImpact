# Non-functional requirements (NFRs)

Targets per stage. Revisit at each phase gate; change via ADR.

| Quality | Stage 2 – pilot | Stage 3 – production |
|---|---|---|
| News-to-score latency (p95) | < 5 min | < 30 s (signals tier) |
| API latency (p95) | < 1 s | < 300 ms |
| Throughput | 10k articles/day | 1M articles/day |
| Availability | best effort (99%) | 99.9% API |
| Data durability | S3 (11 nines) for raw; daily DB backup | PITR, cross-region backup |
| RPO / RTO | 24 h / 24 h | 15 min / 4 h |
| Monthly infra cost | ≤ $40 | budgeted per client |
| Security | SSO, MFA, least-privilege IAM, secrets in SSM, TLS everywhere | + WAF, GuardDuty, SOC 2-ready controls |
| Auditability | every score has `model_version`, `as_of`, source link | immutable audit log, retention policy |
| Reproducibility | point-in-time data, versioned models | + model registry & evaluation reports |
| Observability | structured logs, correlation IDs | OpenTelemetry traces, SLO dashboards, alerts |
| Multi-tenancy | `tenant_id` on events | row-level isolation, per-tenant quotas |
| Test coverage | ≥ 80% lines, contract tests | + load tests, chaos/failure tests |

## Standards we align with

| Area | Standard |
|---|---|
| Architecture docs | C4 model, ADRs |
| App design | 12-Factor App, DDD bounded contexts, hexagonal architecture |
| Cloud | AWS Well-Architected Framework (6 pillars) |
| Contracts | OpenAPI 3.1, CloudEvents 1.0, JSON Schema, SemVer |
| Security | OWASP ASVS, OWASP Top 10 for LLM Applications (news text is untrusted input → prompt injection) |
| Supply chain | Dependabot, pip-audit, Trivy image scanning; SBOM & SLSA later |
| Observability | OpenTelemetry |
| AI governance | NIST AI RMF; model risk management principles (SR 11-7) for finance clients |
| Compliance (later) | SOC 2 / ISO 27001; GDPR/Privacy Act where personal data appears |
