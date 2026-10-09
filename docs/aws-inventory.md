# AWS inventory (planned / tagged)

**Tags:** `Project=SentinelAI-Hackathon`, `SuspensionAt=2026-10-12T06:00:00Z`  
**Account:** `284981582445` **Region:** `us-east-1`

| Resource | Stack | Suspend behavior | Residual cost |
|----------|-------|------------------|---------------|
| Lambda `sentinel-api` | SentinelAI-Api | concurrency 0 + maintenance | code storage |
| API Gateway `sentinel-ai-api` | SentinelAI-Api | idle | negligible |
| Secrets Manager `sentinel-ai/hackathon` | SentinelAI-Api | retain | ~$0.40/mo |
| Lambda `sentinel-suspension-controller` | SentinelAI-Suspension | **never** concurrency 0 | idle |
| Scheduler `sentinel-sunday-suspend` | SentinelAI-Suspension | remains for status/extend | pennies |
| SQS DLQ | SentinelAI-Suspension | retain | idle |
| SSM `sentinel-suspension-state` | runtime | retain | negligible |
| CloudWatch Logs | both | retain (short TTL) | storage |

Update this file after deploy with ARNs from `./scripts/aws-status.sh`.
