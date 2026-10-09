# AWS suspension verification checklist

**Target deadline (UTC):** `2026-10-12T06:00:00Z`  
**Local:** Sunday October 11, 2026 11:00 PM America/Los_Angeles  
**Account (detected):** `284981582445` / `us-east-1`

## Pre-deploy (current)

| Check | Status |
|-------|--------|
| Controller code present (`infrastructure/cdk/suspension_controller`) | IMPLEMENTED |
| CDK suspension stack present | IMPLEMENTED |
| Scripts: status / suspend-now / resume / extend | IMPLEMENTED |
| Cost residual document | IMPLEMENTED (`docs/aws-suspension-and-costs.md`) |
| Live schedule read-back in AWS | **VERIFIED 2026-10-09** — `sentinel-sunday-suspend` ENABLED `at(2026-10-12T06:00:00)` |
| Controller status invoke | **VERIFIED** — preserves_data=true, deletes_resources=false |
| Suspend/resume test on minimal workload | Optional pre-deadline drill via `scripts/aws-suspend-now.sh` / `aws-resume.sh` (do not leave suspended during judging) |

## Post-deploy verification commands

```bash
# 1. Schedule read-back
aws scheduler get-schedule --name sentinel-sunday-suspend --region us-east-1

# Expect: ScheduleExpression at(2026-10-12T06:00:00), State ENABLED

# 2. Controller status
./scripts/aws-status.sh

# 3. Manual suspend (safe — no deletions)
./scripts/aws-suspend-now.sh
# Expect: sentinel-api reserved concurrency 0, maintenance_mode true

# 4. Resume
./scripts/aws-resume.sh

# 5. Extend
NEW_EXPIRY_UTC=2026-10-15T06:00:00Z ./scripts/aws-extend-expiry.sh
# Read back expression matches new expiry
```

## Invariants to prove

1. Schedule target UTC matches `2026-10-12T06:00:00Z` (unless extended).
2. Suspension controller is **excluded** from concurrency-0 list.
3. After suspend: API non-status routes fail closed; GPS/Mongo/OpenAI not invoked.
4. After suspend: CloudFormation stacks, secrets, and external DB data still exist.
5. Resume restores prior concurrency values from SSM state (not “enable everything”).
6. No `cdk destroy` / delete APIs called by controller.

## Sign-off

| Item | Result | Date |
|------|--------|------|
| Schedule UTC verified | PENDING deploy | |
| Manual suspend verified | PENDING deploy | |
| Resume verified | PENDING deploy | |
| Residual cost acknowledged by user | PENDING | |
