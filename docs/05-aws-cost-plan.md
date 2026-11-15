# AWS plan: reliable, secure, and cost-controlled

Principle: **pay per use until revenue justifies always-on.** Costs scale with
clients, not with time. Prices below are approximate (us-east-1, late 2026) –
always confirm with the [AWS Pricing Calculator](https://calculator.aws/).

## Stage 0 – Account hardening (do this first, ≈ $0/month)

Manual, one-time, in the console:

- [ ] Enable **MFA on the root user**; create **no** root access keys; store root credentials offline.
- [ ] Enable **IAM Identity Center**, create your admin user, and use that day to day (never root).
- [ ] Billing → enable *IAM access to billing*, *Cost Explorer*, and check your **Free Tier / credits** status.
- [ ] Set alternate contacts (billing, security).
- [ ] Choose **one primary region** (by client data-residency first, price second; e.g. `us-east-1` is usually cheapest, `ap-southeast-2` if clients require Australian residency).
- [ ] Apply `infra/terraform/bootstrap` → monthly **budget alerts** (25/50/80/100%) + **cost anomaly detection** (free).
- [ ] Enable one **CloudTrail** management-events trail (first copy is free; small S3 cost).

## Stage 1 – Local development (now → working demo): **$0/month**

Everything runs on your laptop (`make dev`, or `make docker`). No cloud needed
until a client must access it.

## Stage 2 – Client demo / pilot environment: target **≈ $5–40/month**

Serverless, scale-to-zero, **no NAT Gateway, no always-on servers**:

| Need | Service | Why | Rough cost |
|---|---|---|---|
| Web app | **S3 + CloudFront** (static SPA) | no servers; CDN scales automatically | ≈ $1 |
| Sign-in | **Amazon Cognito** (OIDC) | free tier covers early users; swappable via OIDC | ≈ $0 |
| API | **Lambda** (container image) + **API Gateway HTTP API** | pay per request | free tier / cents |
| Scheduled ingestion | **EventBridge Scheduler** → Lambda | cron without servers | cents |
| Module-to-module events | **SNS + SQS** (with dead-letter queues) | durable, pay per message | 1M requests free/mo |
| Raw news archive & datasets | **S3** (Parquet), lifecycle → Infrequent Access | cheapest durable storage | ~$0.023/GB-mo |
| Relational + vectors | **Aurora PostgreSQL Serverless v2** with min capacity **0** (auto-pause) + **RDS Data API**, *or* RDS `db.t4g.micro` | SQL + pgvector; Data API means Lambdas need no VPC/NAT | ~$1–15 idle-to-light |
| Secrets | **SSM Parameter Store** (SecureString) | free tier for standard params | ~$0 |
| Logs | **CloudWatch Logs** with **retention = 14–30 days** | unbounded retention is a silent cost | <$5 |
| LLM | `NI_LLM_PRESET`: quality (Claude Opus 5.5) / economy (Claude Haiku 5.5) / local (Ollama); cached, budget-capped gateway | usually the biggest variable cost | `NI_LLM_MONTHLY_BUDGET_USD` (default $5) |
| Market data | EODHD end-of-day, US + ASX (commercial licence for client use) | one vendor for both markets | ≈ $20/mo (personal); commercial: quote |
| Container images | **ECR** with lifecycle policy (keep last 10) | | <$1 |

## Stage 3 – Paying clients / production: funded by revenue

Separate AWS accounts via **AWS Organizations** (management / dev / prod),
**ECS Fargate** behind an ALB for steady traffic, **Aurora Multi-AZ**,
WAF, GuardDuty, backups with tested restores, OpenTelemetry tracing.
Expect roughly $200–800/month depending on volume – introduce only when
SLAs or client contracts require it.

## Cost traps to avoid (common with new AWS accounts)

| Trap | Cost | Alternative |
|---|---|---|
| **NAT Gateway** (any private-subnet design) | ~$32/mo each + $0.045/GB | Lambdas outside VPC + RDS Data API, VPC endpoints, or a NAT instance |
| **EKS** control plane | ~$73/mo before any workload | Lambda / ECS Fargate |
| **MSK (Kafka)**, **OpenSearch** clusters | $100s/mo | SQS/SNS/EventBridge; pgvector |
| Idle **ALB** | ~$16+/mo | API Gateway HTTP API |
| Public **IPv4 addresses** | ~$3.6/mo each | fewer public endpoints |
| CloudWatch Logs without retention | grows forever | set retention in Terraform |
| Forgotten dev resources | anything | everything via Terraform + `Project`/`Env` tags; `terraform destroy` dev when idle |
| Unbounded LLM calls on every article | can exceed all infra cost | cheap filter first, LLM for high-value items, cache by content hash, monthly cap |

## Terraform layout (planned)

```
infra/terraform/
  bootstrap/        ✅ budgets + anomaly detection (local state)
  modules/          reusable: lambda_service, queue_with_dlq, aurora_serverless, s3_datalake
  envs/dev/         composes modules; S3 backend with lockfile
  envs/prod/
```
