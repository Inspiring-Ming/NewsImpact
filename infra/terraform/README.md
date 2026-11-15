# Infrastructure (Terraform)

Nothing here runs automatically. You apply it yourself, deliberately.

## 1. Bootstrap (cost guardrails) – do this first

Creates: a monthly AWS Budget with email alerts, and Cost Anomaly Detection.
Both are free or near-free.

```bash
# prerequisites: terraform >= 1.6, AWS CLI, and an IAM Identity Center login
aws configure sso            # one time
aws sso login

cd infra/terraform/bootstrap
cp example.tfvars terraform.tfvars   # edit alert email + budget
terraform init
terraform plan               # review: should show 3 resources to add
terraform apply
```

Confirm the subscription emails AWS sends you.

## 2. Application stacks (later – Phase 4)

`modules/` and `envs/dev|prod` will be added when the first client demo needs
cloud hosting. See [../../docs/05-aws-cost-plan.md](../../docs/05-aws-cost-plan.md).
