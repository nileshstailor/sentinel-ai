# AWS suspension and residual costs

**Scheduled suspend:** Sunday October 11, 2026, 11:00 PM America/Los_Angeles → `2026-10-12T06:00:00Z`  
**Mode:** Reversible **suspension** (disable invocations). **No automatic deletion** of stacks, databases, secrets, logs, or GPS history.  
**AWS Budgets:** Advisory notifications only — **not a hard financial cap**.

## What suspension does

| Control | Effect |
|---------|--------|
| Lambda reserved concurrency → 0 | Blocks new invocations for project functions (except suspension controller) |
| `SENTINEL_MAINTENANCE_MODE=true` | API returns 503 for non-status routes |
| Event source mappings disabled | Stops stream/queue triggers |
| EventBridge rules disabled | Stops scheduled project rules |
| EventBridge Scheduler one-time schedule | Fires suspend at deadline; controller remains operable |

## What suspension does **not** do

- Does **not** run `cdk destroy` or delete CloudFormation stacks
- Does **not** delete ClickHouse / MongoDB / Secrets / logs / GPS history
- Does **not** stop third-party platform billing (OpenAI, ClickHouse Cloud, MongoDB Atlas, ElevenLabs)
- Does **not** guarantee a $0 AWS bill

## Residual AWS charges while suspended (estimated, us-east-1)

| Resource | Why it still costs | Rough order of magnitude |
|----------|--------------------|--------------------------|
| Secrets Manager secret | Per-secret monthly + API calls | ~$0.40/secret/month |
| CloudWatch Logs (retained) | Ingestion stopped; storage retained (7–14 day retention configured) | Cents–low dollars depending on volume |
| API Gateway REST API definition | Idle API still exists | Typically negligible when unused |
| Lambda function (idle) | No invoke charges when concurrency=0 | $0 invoke; tiny storage for code |
| EventBridge Scheduler schedule | One-time / schedule object | Pennies |
| Suspension controller Lambda + DLQ | Must remain operable | Near $0 when idle + SQS idle |
| SSM Parameter (suspension state) | Standard parameter | Free tier / negligible |
| AWS Budgets | Budget object | Free for first budgets; notifications may use SNS |

**Prefer pay-per-request:** Lambda + API Gateway + Secrets + ClickHouse Cloud / MongoDB Atlas (external). Avoid NAT Gateways, always-on EC2, provisioned concurrency, and EIPs unless explicitly approved.

## Third-party costs (outside AWS)

| Provider | During Sentinel suspend | How to pause on provider side |
|----------|-------------------------|-------------------------------|
| OpenAI | No new calls from Sentinel | Rotate/disable API key; check OpenAI billing limits |
| ClickHouse Cloud | Storage may continue | Use ClickHouse idle/scale controls per their plan; do not delete GPS without user consent |
| MongoDB Atlas | Cluster idle charges may continue | Pause cluster in Atlas UI if available on tier |
| ElevenLabs | No calls when disabled | Disable key / pause workspace |

## Scripts

```bash
./scripts/aws-status.sh
./scripts/aws-suspend-now.sh
./scripts/aws-resume.sh
NEW_EXPIRY_UTC=2026-10-18T06:00:00Z ./scripts/aws-extend-expiry.sh
NEW_EXPIRY_UTC=2026-10-18T06:00:00Z ./scripts/aws-resume.sh   # if past deadline
```

## Approval required before provision

Deploying creates billable resources with residual costs above even when suspended. Obtain explicit max spend and email for budget alerts before `cdk deploy`.
