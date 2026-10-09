# Sentinel AI

**Your Money Has a Bodyguard.**

Native SwiftUI iPhone app + AWS-hosted autonomous fraud agent that investigates risky activity with real GPS evidence, freezes a functional mock bank when policy allows, and verifies the freeze by rejecting the next transfer.

Built for the [Tokens& Cyberdefense Hackathon](https://tokensand.com/cyberhack).

---

## 1. Problem Statement

Account takeovers and payment fraud often look like “normal” digital banking: a new device, a password reset, a late restaurant charge, an online purchase with a foreign merchant label. Traditional alerts either fire too late, cry wolf on harmless travel/online shopping, or ask the customer to call a hotline while money is already moving.

Delayed card posting makes this worse—restaurant bills can appear days after you left the table—so location at charge time and location at post time are not the same problem.

## 2. Our Solution

**Sentinel AI** watches for high-risk patterns, gathers evidence autonomously, and—when a deterministic policy approves—restricts a mock bank account, then proves the restriction worked.

| Layer | What it does |
|-------|----------------|
| iPhone (SwiftUI) | Live Core Location, alerts, Face ID for freeze/unfreeze, Demo Lab |
| AWS API Gateway + Lambda | FastAPI fraud pipeline (production demo host) |
| OpenAI | Tool-calling investigator (evidence gathering + structured conclusion) |
| ClickHouse | GPS + event analytics that inform risk |
| MongoDB | Incidents, policies, mock-bank state |
| ElevenLabs | Live TTS for an AI fraud-hotline escalation voice |

## 3. Why Sentinel AI Is Different

- **Agentic, not chatty:** OpenAI investigates with tools; the customer does not prompt the investigation.
- **Grounded in body location:** Real iPhone GPS in ClickHouse informs restaurant verification and travel context.
- **Policy before power:** The LLM cannot freely freeze accounts. A deterministic policy authorizes mock-bank restrictions.
- **Verified action:** After a freeze, a follow-up transfer must return `rejected_restricted`.
- **Consumer clarity:** Statuses like **Verified**, **Needs review**, and **Account protected**—with Face ID before freeze/unfreeze.

## 4. Key Features

- Native iOS 17+ SwiftUI app (Home, Activity, Alerts, Location, Demo Lab)
- Permissioned GPS upload to AWS → ClickHouse
- Autonomous investigation on scenario/event ingest
- Mock-bank freeze + transfer rejection proof
- Local time-sensitive notifications for urgent alerts
- ElevenLabs live TTS for disclosed AI fraud-hotline speech
- Scheduled reversible AWS suspend (preserve data; no auto-delete)

## 5. Autonomous Agent Architecture

```
Event ingest → preliminary screening → OpenAI tool investigation
  → structured conclusion + evidence refs
  → SecurityPolicyEngine (deterministic)
  → authorized mock-bank restrict (optional)
  → verify bank state → notify user
```

Tools include transaction lookup, location history, merchant-to-visit matching, security events, trusted devices, policy checks, protection request/status, escalation, and investigation recording.

See [`docs/architecture.md`](docs/architecture.md) for the Mermaid diagram and trust boundaries.

## 6. Sponsor Integrations

| Sponsor | Role in this MVP | Status (verified 2026-10-09) |
|---------|------------------|------------------------------|
| **AWS** | API Gateway, Lambda, Secrets Manager, EventBridge Scheduler, Budgets | Live |
| **OpenAI** | Tool-calling fraud investigator | Live |
| **ClickHouse** | GPS / event analytics | Live |
| **MongoDB** | Incidents + mock-bank persistence | Live |
| **ElevenLabs** | Live TTS fraud-hotline voice generation | Live (TTS; not full PSTN dial) |

Public health check (no auth):  
`https://8m6o4go9oc.execute-api.us-east-1.amazonaws.com/prod/health`

## 7. System Architecture

```text
┌─────────────────┐     HTTPS      ┌──────────────────┐
│  SwiftUI iPhone │ ─────────────► │  API Gateway     │
│  Core Location  │                │  + Lambda/FastAPI│
└─────────────────┘                └────────┬─────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              ▼                             ▼                             ▼
        ClickHouse                    OpenAI Agent                   MongoDB
     (GPS / events)                (tool investigation)         (incidents / bank)
                                            │
                                            ▼
                                   Policy engine → Mock bank
                                            │
                                            ▼
                                   ElevenLabs TTS (stretch)
```

Independent **Suspension** stack: EventBridge Scheduler → controller Lambda (no deletions).

## 8. Demo Scenarios

Use **Demo Lab** (reset first if the account is already frozen):

1. **Stolen phone — Freeze account** → Account protected; bank restricted  
2. **Attempt transfer after takeover** → `rejected_restricted` (key proof)  
3. **Restaurant — Should Verify / Needs Review** → GPS match vs insufficient evidence  
4. **Colombia online / card-present** → review vs higher risk without auto-freezing every foreign label  
5. **Generate AI hotline voice** → live ElevenLabs TTS bytes  

Narration and shot list: [`submission/DEMO_SCRIPT.md`](submission/DEMO_SCRIPT.md).

## 9. Technology Stack

- **iOS:** Swift 6, SwiftUI, Core Location, LocalAuthentication, UserNotifications  
- **Backend:** Python 3.12, FastAPI, Pydantic, Mangum  
- **Cloud:** AWS CDK, API Gateway, Lambda, Secrets Manager, EventBridge Scheduler, Budgets  
- **Data:** ClickHouse Cloud, MongoDB Atlas  
- **AI / voice:** OpenAI, ElevenLabs  

## 10. Installation and Configuration

### Prerequisites

- Xcode 16+, iOS 17+ device recommended for GPS / Face ID  
- Python 3.12+, AWS CLI (for ops scripts)  
- Sponsor credentials in local `.env` (never commit) and/or Secrets Manager `sentinel-ai/hackathon`

### Backend tests (local)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env   # fill locally; do not commit
cd backend && pytest -q
```

### iOS

```bash
cd ios/SentinelAI && xcodegen generate   # if regenerating
open SentinelAI.xcodeproj
```

1. Select Team **FNQB5S99AA** (or your team).  
2. Do **not** commit real API tokens. Use Demo Lab → paste token → **Save & Sync**, or copy `Config.local.plist.example` → `Config.local.plist` (gitignored).  
3. Allow Location and Notifications when prompted.

### Secrets

- Template: [`.env.example`](.env.example)  
- iOS local override example: [`ios/SentinelAI/SentinelAI/Config.local.plist.example`](ios/SentinelAI/SentinelAI/Config.local.plist.example)  
- See [`docs/security.md`](docs/security.md)

## 11. AWS Infrastructure

| Resource | Name / note |
|----------|-------------|
| API | `https://8m6o4go9oc.execute-api.us-east-1.amazonaws.com/prod/` |
| Lambda | `sentinel-api` |
| Secrets | `sentinel-ai/hackathon` |
| Suspend schedule | `sentinel-sunday-suspend` = `at(2026-10-12T06:00:00)` UTC **ENABLED** |
| Budget | `SentinelAI-Hackathon-300` (advisory) |

Ops scripts: `scripts/aws-status.sh`, `aws-suspend-now.sh`, `aws-resume.sh`, `aws-extend-expiry.sh`.

**Suspend deadline:** Sunday Oct 11, 2026 11:00 PM America/Los_Angeles (`2026-10-12T06:00:00Z`).  
Suspend disables ingress/compute paths; **does not delete** stacks, DBs, GPS, secrets, or logs. Residual costs: [`docs/aws-suspension-and-costs.md`](docs/aws-suspension-and-costs.md).

## 12. Security and Privacy

- Bearer token auth for hackathon (Cognito-ready later)  
- Tenant isolation by `user_id`  
- Face ID before freeze / unfreeze / hotline escalation  
- LLM cannot directly execute bank freezes  
- GPS under user control; deletion via API; not tied to AWS suspend  
- No real FI credentials; mock bank only  

## 13. Real vs Simulated Functionality

| Capability | Mode |
|------------|------|
| iPhone GPS capture & upload | **Real** |
| AWS API / Lambda hosting | **Real** |
| OpenAI investigation calls | **Real** (when key configured — currently live) |
| ClickHouse GPS storage/query | **Real** (live) |
| MongoDB persistence | **Real** (live) |
| ElevenLabs TTS generation | **Real** (live TTS; not full outbound PSTN) |
| Bank balance, transfers, freezes | **Simulated** functional mock bank |
| Fraud-hotline phone call to a carrier | **Not deployed** (TTS stretch only) |

## 14. Known Limitations

- Mock bank ≠ real financial institution  
- ElevenLabs stretch = live TTS generation, not completed PSTN dial  
- Background GPS is best-effort; foreground is reliable  
- Notifications are local/device-triggered, not a full APNs product  
- Public incident API omits raw `tool_trace` (consumer fields only)  
- Dev bearer token auth (not Cognito)  
- One local pytest historically assumed `tool_trace` on public payloads — updated for consumer contract  

## 15. Future Roadmap

- Real FI / payment-network partnerships (with contractual scopes)  
- Full ElevenLabs Agents telephony to a controlled hotline  
- Cognito / passkeys for consumer auth  
- Richer SOC evidence timeline for analysts  
- Broader fraud typologies beyond the three hackathon scenarios  

## 16. Team

| Role | Name | Contact |
|------|------|---------|
| TBD | TBD | TBD |

*(Fill before form submit — do not invent teammates.)*

---

## Docs index

| Doc | Purpose |
|-----|---------|
| [`docs/architecture.md`](docs/architecture.md) | Mermaid architecture + trust boundaries |
| [`docs/security.md`](docs/security.md) | Security notes |
| [`docs/demo.md`](docs/demo.md) | Demo ops notes |
| [`submission/`](submission/) | Hackathon submission package |
| [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) | Deployment status snapshot |

## License / hackathon use

Hackathon MVP. Do not treat as a production banking product.
