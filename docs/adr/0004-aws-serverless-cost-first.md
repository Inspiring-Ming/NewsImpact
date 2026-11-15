# 0004 – AWS, serverless and scale-to-zero first

* Status: accepted
* Date: 2026-11-14

## Context
Founder-funded AWS account; demand is unknown; reliability still matters
for client demos.

## Decision
Develop locally at $0. First cloud environment uses Lambda, API Gateway HTTP
API, SNS/SQS with DLQs, S3, Aurora Serverless v2 (min 0 ACU) with Data API
(or RDS t4g.micro), SSM Parameter Store. Avoid NAT Gateway, EKS, MSK,
OpenSearch, idle ALBs. Budgets + anomaly detection applied before any
other resource. All infra in Terraform with Project/Env tags.

## Consequences
+ Near-zero idle cost; managed services give reliability without ops staff.
− Cold starts (seconds) after idle; acceptable for demos/reports, not for
  low-latency trading → revisit with ECS Fargate when an SLA requires it.
+ Portability preserved: containers, Postgres, Parquet, and ports/adapters.
