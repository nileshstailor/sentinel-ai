# Project Description — Sentinel AI

### Project Name
Sentinel AI

### Tagline
Your Money Has a Bodyguard.

### Elevator Pitch
Sentinel AI is an autonomous cyberdefense agent on your iPhone that investigates risky banking activity with real GPS evidence, freezes a mock account when policy allows, and proves the freeze by blocking the next transfer.

### Short Description
Sentinel AI pairs a native SwiftUI iPhone app with an AWS-hosted FastAPI agent. Real iPhone GPS lands in ClickHouse; OpenAI investigates with tools; MongoDB persists incidents and mock-bank state; a deterministic policy authorizes freezes; ElevenLabs generates live fraud-hotline TTS. Built for the Tokens& Cyberdefense Hackathon.

### Full Description
Financial fraud rarely announces itself. A stolen phone, a new device login, a late restaurant charge, or an online purchase with a foreign merchant label can look routine until money moves. Sentinel AI watches those moments without waiting for the customer to open a chatbot.

When a high-risk pattern appears, an OpenAI tool-calling investigator gathers evidence—transactions, security events, and location analytics from ClickHouse—then returns a structured conclusion. A separate deterministic policy decides whether the functional mock bank may be restricted. If a freeze is authorized, Sentinel verifies the bank state and surfaces an **Account protected** alert. The customer can prove the freeze by attempting another transfer and seeing `rejected_restricted`. Softer cases become **Needs review** or **Verified**, especially when restaurant charges line up with where the phone actually was.

The iPhone app is native SwiftUI: live Core Location, consumer-friendly alerts, Face ID before freeze or unfreeze, and a Demo Lab for hackathon scenarios. ElevenLabs supplies live text-to-speech for an AI fraud-hotline escalation voice. Everything customer-facing runs against AWS API Gateway and Lambda—not a localhost demo backend—with a scheduled reversible suspend that preserves data after the hackathon window.

### Problem
Account takeover and payment fraud exploit digital banking speed. Delayed posting blurs restaurant truth. Traditional alerts either spam customers on harmless foreign-labeled online orders or ask them to call a hotline while an attacker drains funds. Location, device, and transfer signals are rarely combined into an agent that both investigates and *acts*, then proves the action worked.

### Solution
Autonomous investigation grounded in iPhone GPS and event analytics; consumer statuses that reduce noise; protective mock-bank restriction only after policy approval; verified transfer rejection; optional AI hotline voice via ElevenLabs.

### What Makes It Agentic
The customer does not drive a chat loop. Event ingest (or a Demo Lab scenario) triggers bounded OpenAI tool use: fetch transaction details, query location history, match merchants to visits, inspect security events, and more. The agent produces a structured conclusion with evidence references. Protective freezes are executed only through authorized services and verified against mock-bank state afterward.

### Sponsor Integrations

| Sponsor | Actual role in MVP |
|---------|--------------------|
| **OpenAI** | Live tool-calling investigation and structured conclusions |
| **ClickHouse** | Live GPS and event analytics informing risk |
| **MongoDB** | Persistent incidents, policies, mock-bank account state |
| **AWS** | API Gateway, Lambda, Secrets Manager, Scheduler, Budgets |
| **ElevenLabs** | Live TTS generation for disclosed AI fraud-hotline speech |

### Security Boundaries
The investigator LLM cannot directly freeze accounts. `SecurityPolicyEngine` must authorize restrict/unrestrict. Face ID gates freeze/unfreeze/hotline UI actions. Public APIs expose consumer incident fields, not raw tool traces. Suspension disables workloads without deleting data stores.

### What Is Simulated
Bank accounts, balances, recipients, transfers, and account restrictions operate against a **functional mock bank**. No real financial institution is moved or frozen.

### What Is Real
iOS GPS capture and upload; AWS-hosted API; live OpenAI, ClickHouse, MongoDB, and ElevenLabs TTS (when configured—verified live for the hackathon deploy); incident persistence; investigation tools; policy checks; freeze verification via rejected transfers; local urgent notifications.

### Future Vision
Real bank partnerships, payment-network integrations, expanded fraud typologies, Cognito-grade consumer auth, and actual fraud-hotline telephony via ElevenLabs Agents. **None of these future items are claimed as deployed today.**
