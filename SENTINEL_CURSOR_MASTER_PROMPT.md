# SENTINEL AI — CURSOR IMPLEMENTATION MASTER PROMPT

You are acting as a senior iOS engineer, AWS architect, Python backend engineer, autonomous-agent engineer, application-security engineer, designer, and QA engineer. BUILD, RUN, TEST, and DOCUMENT a working same-day hackathon MVP, not merely an architecture proposal.

## Mission and constraints

**Name:** Sentinel AI  
**Tagline:** Your money has a bodyguard.  
**Hackathon challenge:** Ship an autonomous agent that takes genuine, grounded actions, preserves what matters, and integrates at least three sponsor tools.

Create a native SwiftUI iPhone app with actual permissioned GPS tracking, a backend deployed on AWS where practical, real ClickHouse location/event analytics, real OpenAI tool-using investigations, MongoDB incident/policy persistence, and an optional ElevenLabs emergency voice demo. Bank accounts, bank logins, and payment transfers are SYNTHETIC. A protective freeze must execute on a functioning mock bank and be verified by an attempted second transfer.

Build a polished, runnable end-to-end vertical slice FIRST; do not spend the demo window on unnecessary infrastructure. Never claim a synthetic bank action affected a real bank. Never deploy or incur cloud charges without explicit approval. Never commit credentials.

## CRITICAL: AWS-ONLY DEPLOYMENT, REVERSIBLE SUSPENSION, AND COST GUARDRAILS

**Deadline: Sunday, October 11, 2026 at 11:00 PM America/Los_Angeles (2026-10-12T06:00:00Z).** At this time suspend **this project's operational workloads** automatically unless the user explicitly orders an earlier suspension or authorizes an extension. **Do not delete AWS stacks, databases, secrets, logs, location data, or application files as part of the automatic suspension.** No automatic `cdk destroy`, stack deletion, resource deletion, or database deletion. Destructive cleanup is a separate opt-in operation requiring fresh explicit consent.

**Cloud-only requirement:** The app must use an AWS-hosted backend for actual end-to-end operation and the demo. Do NOT present localhost, an on-device mock backend, LocalStack, or local FastAPI as the target deployment or a fallback. Local linting, compilation, unit tests, and CDK synth are permitted, but functional acceptance must use the live AWS API and genuine sponsor integrations. If cloud credentials/approval are missing, report the blocker and continue with deployable code; don't pretend it works.

Implement and verify these controls *before enabling any chargeable AWS workload*:

1. **Isolation and inventory:** Dedicated Sentinel project stack(s), tags `Project=SentinelAI-Hackathon`, `SuspensionAt=2026-10-12T06:00:00Z`, account/region inventory and resource-by-resource cost exposure. Never change unrelated services.
2. **AWS budgets and limits:** Obtain an explicit maximum authorized spend, apply AWS Budgets notifications at 50%, 80%, and 100%, CloudWatch alarms where useful, API rate throttles, bounded Lambda concurrency and timeouts, Step Functions limits, queue limits/retention, and log retention. AWS Budgets are advisory, **not a hard financial cap**. Avoid always-on compute, expensive NAT gateways, unnecessary provisioned capacity, and EIPs.
3. **Reversible SUSPEND controller:** A one-time Amazon EventBridge Scheduler schedule for the stated UTC deadline invokes an independently hosted, least-privileged suspension controller. It must first set project maintenance/deny-new-work state and then disable ONLY inventoried Sentinel ingress, triggers, event-source mappings, EventBridge rules, schedules, Step Functions starts, and other project workloads; set Lambda reserved concurrency to 0 where safe and supported; pause/scale-to-zero only services that actually offer it. Disable ingestion and agent calls to avoid sponsor API charges. Preserve application definitions and stored data. Ensure the suspension controller and status/restart mechanism remain operable after suspension and don't block their own execution. Implement idempotency, retries, DLQ or failure alarm, and read-back verification. Make no false claim that a project is suspended until the controls are confirmed.
4. **Resume, stop-early, and extend:** Create `scripts/aws-suspend-now.sh`, `scripts/aws-resume.sh`, `scripts/aws-extend-expiry.sh`, and `scripts/aws-status.sh`. Restore previously captured triggers/concurrency settings on resume; do not blindly enable everything. Resuming after expiration requires an explicitly approved new expiry and spend allowance. Extension must update the actual schedule and verify it. No LLM or runtime user may secretly alter expiry. Never delete data when running any of these commands.
5. **Costs that cannot be fully paused:** Some AWS services (storage, Secrets Manager, CloudWatch logs, static hosting, provisioned database/network resources, Scheduler/watchdog) may continue charging while suspended. Some cannot be 'turned off' without deletion. Enumerate each residual resource, estimated ongoing cost, and feasible preservation alternatives in `docs/aws-suspension-and-costs.md`. For services that cannot pause, prefer genuinely pay-per-request or low-cost persistence. Do not promise a $0 bill. Explicitly ask user consent before provisioning an unavoidable continuing-cost component; if not approved, omit that component and report the limitation.
6. **Third-party billing:** MongoDB Atlas, ClickHouse Cloud, ElevenLabs, and OpenAI are outside AWS. Suspend Sentinel's external requests, but do not claim to stop their platform charges or turn off their resources. Document separate provider-side pause mechanisms and costs. Do not delete their data. Seek user approval for any changes to provider billing state.
7. **Verification:** Read back Scheduler target and UTC date, permissions, tagged resource inventory, preserved storage, and actual disabled invocation paths. Validate suspend/resume on a minimal test workload without deleting production resources. Generate `docs/aws-suspension-verification.md`, plus warnings and confirmation if any expensive chargeable resource will remain running.
8. **Protected data:** Preserve ClickHouse GPS history, MongoDB incidents and settings, and all other user data during suspension, subject only to independently disclosed and explicitly authorized data-retention rules. Do not set a short GPS TTL by surprise. Provide privacy controls for the user to delete their own data, but never tie deletion to the shutdown deadline.

IMPORTANT: Suspension does not guarantee zero cost or eliminate all external service charges; enumerate residual charges plainly. If reliable suspension cannot be proven, DO NOT deploy chargeable resources without explicitly explaining the blocker and obtaining fresh consent. The system remains AWS-hosted, not local.

## Architecture

**iOS:** Swift 6 / SwiftUI (iOS 17+), Core Location, MapKit, Face ID with LocalAuthentication, UserNotifications, URLSession async/await, Keychain. Native, dark, premium, accessible dashboard.

**Backend:** Python 3.12+, FastAPI, Pydantic, Pytest. Shared Python business logic deployed to AWS Lambda; local execution is for automated tests only, never the hosted demo. API Gateway, Lambda, EventBridge, SQS, Step Functions (only where justified), Cognito or secure development auth, CloudWatch, Secrets Manager, IAM, AWS CDK. Avoid building an overcomplicated microservice system: one coherent working fraud workflow matters more.

**Sponsors:**
- OpenAI: real structured tool-calling autonomous investigation and explanations grounded in referenced evidence.
- ClickHouse Cloud: REAL GPS observations from the iPhone plus synthetic financial/authentication events; geospatial and time-window analytics must actively inform risk detection.
- MongoDB Atlas: trusted devices, travel plans, preferences, policies, incidents, approvals, and action state.
- ElevenLabs (stretch): disclosed AI assistant calls a mock bank fraud hotline; no cloning user's voice to impersonate or defeat bank verification.
- AWS: primary runtime/orchestration, deployment managed with CDK and expiration safeguards.

Do not count a sponsor as integrated merely because it is listed in a diagram. Use real APIs when credentials provided; otherwise preserve clean interface and label the test adapter as simulated.

## Core iOS screens

1. **Home:** protection summary, last actual GPS fix with accuracy/time, bank status (DEMO), counts of reviewed/suspicious transactions, urgent incidents, recent agent actions.
2. **Transactions:** synthetic transaction feed with merchant, channel, amount, authorization date, posting date, likely purchase interval, explanation and verification state.
3. **Location Vault:** real permissioned iPhone location readings recorded in ClickHouse via authenticated backend, map and history, precision, sync freshness, pause/resume and delete controls. Prioritize foreground location; add visit and significant-change APIs if time and entitlements permit. Never assume uninterrupted background collection.
4. **Incident Timeline:** evidence IDs, what ClickHouse found, agent tool-call traces, uncertainty, proposed and actual actions, confirmation/failed status.
5. **Fraud Inbox:** quiet everyday monitoring, bundled uncertain charges, immediately surfaced high-risk incidents; avoid alert fatigue.
6. **Security/Travel:** manually entered flight/cruise/hotel plans, trusted devices, Face ID approval, retention policy, source permissions, clear DEMO labels.
7. **Demo Lab:** scenario launch buttons that inject synthetic bank events into the SAME actual event/agent/policy pipeline.

## ClickHouse design and query requirements

Use tables or migration scripts for:
- `gps_events`: event_id, user_id, device_id, event_timestamp UTC, lat, lon, horizontal_accuracy_m, source, received_at UTC, synthetic flag (false for genuine iPhone capture).
- `financial_events`: account_id, event_id, transaction type/channel (card-present, card-not-present, Zelle-like transfer, Venmo-like transfer), merchant, merchant geo when reliably known, amount/currency, authorization and posting times, synthetic=true.
- `security_events`: login, new device, failed login, MFA/recovery changes, new beneficiary, timestamps, device/source location, synthetic=true.
- `agent_telemetry`: incident/action/tool status and evidence references.

Query per user with proper tenant isolation. Use suitable MergeTree sorting, partitions and TTL (30 days default for GPS, adjustable); use `greatCircleDistance` or equivalent and incorporate horizontal accuracy, merchant geocoding confidence, time windows, and data freshness. Never infer that **absence** of a location record proves the user never visited somewhere. Do not export whole GPS histories to OpenAI: share a minimized, derived evidence summary.

## The autonomous agent: what makes it an agent

An incoming event triggers a bounded OpenAI-driven investigation without the customer needing to prompt it. Implement typed tools:
`get_transaction_details`, `query_location_history`, `match_merchant_to_visits`, `get_travel_context`, `get_security_events`, `get_trusted_devices`, `get_policy`, `get_related_activity`, `request_user_verification`, `request_protection`, `check_protection_status`, `escalate_fraud_incident`, `record_investigation`.

Flow: ingest -> deterministic preliminary screening -> agent gathers evidence via actual tools -> structured conclusion with evidence IDs, competing explanations and missing data -> separate deterministic policy approves/denies protective actions -> authorized service acts -> verify backend state -> record telemetry -> alert only if relevant. Implement retries/idempotency. Treat external descriptions/receipts as untrusted and resist prompt injection. Never let an LLM directly freeze accounts, change credentials, or suppress auditing.

Response levels:
0 allow/log, 1 silent investigation, 2 customer review, 3 narrow temporary restriction if preauthorized and supported, 4 emergency fraud escalation. Scores are illustrative heuristics, not calibrated fraud probabilities. Silence is not proof of wrongdoing.

## Functional mock bank

Create actual backend persistent state for synthetic accounts/balances/recipients/auth sessions/transfer states. Endpoints for synthetic transaction, login, MFA change, new recipient, transfer attempt, restrict/unrestrict, restriction-status read, and dispute initiation. Authorization and audit trails apply even to demo endpoints. A restricted demo account MUST reject subsequent transfers; verify by reading returned response. Never label a demo restriction as a real bank freeze or reversal.

## Three required scenarios

**A. Delayed restaurant posting, SF trip:** customer traveled Miami -> San Francisco, a restaurant charge posts several days after purchase. Use authorization time if available; otherwise use a reasonable configurable lookback (demo 7-14 days) with uncertainty. Query real ClickHouse GPS history against merchant location, visit times, and accuracy. Produce one supported match and one insufficient-evidence case. Usually silent verification or a digest, not automatic accusation.

**B. Foreign Colombia anomaly:** SF phone location versus synthetic Colombia card-present, online merchant, or new-beneficiary transfer. Distinguish transaction channels and do not treat Colombian merchant online charges as proof of fraud. Escalate only on multiple strong signals such as new device + MFA change + new recipient.

**C. Stolen phone/account takeover:** synthetic device compromise, risky transfer, recipient change and MFA changes. Agent gathers evidence, policy invokes real code to restrict mock bank, next mock transfer is rejected, and incident timeline proves it. A stolen primary phone cannot be sole trusted approval device; demonstrate backup-trust/recovery path.

**Stretch D. ElevenLabs SOS:** if API credentials and telephony are available, make a real call to a controlled mock fraud hotline. Clearly identify the AI assistant. No voice impersonation, bypass of bank KYC, recording without lawful consent, real-bank phone calls, or unsupported claims of freeze/reversal. Log sanitized result.

## Data safety

Implement authentication and tenant isolation; TLS in cloud; secrets only in Secrets Manager or local untracked `.env`; encrypted storage; rate limits; permissions and provenance; concise auditable evidence; location deletion and pause; explicit user consent; no collection of bank passwords or OTPs; no unconsented message/search history surveillance. Sensitive action approval requires authenticated session, registered device, transaction-specific authorization and recovery fallback; Face ID alone is not bank authorization. Document that the location of a stolen phone is not reliable proof of owner presence.

## Monorepo layout

```
sentinel-ai/
  ios/SentinelAI/                  # native source and reproducible Xcode project
  backend/app/{api,agents,analytics,policies,integrations,simulation,models,services}/
  backend/tests/
  infrastructure/cdk/
  scripts/{setup.sh,seed_demo.py,run_demo.py,aws-stop-now.sh,aws-extend-expiry.sh,aws-status.sh}
  docs/{architecture.md,security.md,demo.md,aws-inventory.md,aws-suspension-verification.md,aws-suspension-and-costs.md,external-services-cleanup.md}
  .env.example
  README.md
  IMPLEMENTATION_STATUS.md
```

## Build sequence — do not stall

1. Inspect actual repo, macOS/Xcode, AWS CLI, Python and credential availability. Write `IMPLEMENTATION_STATUS.md` with truthful statuses.
2. Build the mock-bank service as AWS-deployable Lambda/FastAPI code, synthetic seed data, tests, and native SwiftUI starter UI. No localhost demo fallback.
3. Real Core Location -> FastAPI -> ClickHouse insert/query -> iOS map. Verify a real iPhone observation if the device is connected.
4. Synthetic finance/security events -> ClickHouse SQL detection -> OpenAI agent tools -> deterministic policy -> mock bank lock -> prove subsequent transfer rejection -> incident timeline.
5. MongoDB trusted context/policy/incidents, integrated with the pipeline. Make all 3 sponsor API calls real where credentials exist.
6. Wire notification and Face ID review; demo all three scenarios.
7. Prepare CDK deployment and **fully configured/verified reversible Sunday suspension controls BEFORE any user-approved deployment**. The end-to-end demo MUST run on AWS, not localhost. Avoid persistent charges without explicit approval.
8. If time remains, ElevenLabs mock fraud phone call.
9. Test iOS build, backend tests, endpoint smoke tests, safety tests, synthetic event end-to-end tests, and infrastructure synthesis. Fix issues.
10. Produce short live-demo instructions and 2-minute hackathon pitch.

## Tests/acceptance checks

- SwiftUI project opens and builds; no fictitious compilation claims.
- iPhone GPS captures actual coordinates with permission, sends to backend, and queries back from ClickHouse with timestamps and accuracy.
- Restaurant temporal/geospatial matching handles missed points, delayed postings and inaccurate GPS.
- Colombia online merchant and legitimate travel do not automatically cause freezes.
- Account takeover causes real mock-bank restriction, and a subsequent synthetic transfer is blocked.
- Actual OpenAI agent tool traces and evidence-linked explanation are visible.
- Actual MongoDB and ClickHouse operations demonstrated, or clearly listed as blocked if credentials missing.
- A failed restriction is never shown as successful.
- An AWS-approved deployment must have a verified Sunday, Oct 11, 2026 11 PM Pacific reversible suspension, budget alerts, scoped pause/resume controls, preserved data, and an explicit inventory of charges that continue. If not verified, DO NOT DEPLOY.
- Provide exact commands and honest proof in docs and implementation status.

## First action

Read this complete brief, inspect the environment, write a concise plan and current status, then **start creating real files and running code immediately**. Continue through the highest-priority working slice. Do not stop at planning or cosmetic screens. Ask only about unavoidable credentials, iOS signing, approved cloud spend cap, or approval for persistent residual charges. Never schedule automatic GPS data deletion. Make no unapproved cloud modifications.
