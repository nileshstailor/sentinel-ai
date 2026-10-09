# Judge Q&A — Sentinel AI

Short, honest answers aligned with the deployed MVP.

### 1. What makes this an autonomous agent?
Event ingest triggers a bounded OpenAI tool-calling investigation without the user prompting a chat. The agent gathers evidence, returns a structured conclusion, and downstream services may act—then we verify mock-bank state.

### 2. Isn't this just fraud detection with an LLM?
Detection alone stops at a score. Sentinel adds tool use against GPS/events, a **deterministic policy** gate, an enforceable mock-bank freeze, and a **verified** rejected transfer. The LLM does not directly hold the freeze switch.

### 3. How does the agent decide what to investigate?
Incoming financial/security events (or Demo Lab scenarios) enter the same pipeline. Preliminary screening plus the investigator’s tool loop fetch transactions, location history, merchant-visit matches, security events, and related context before concluding.

### 4. Why do you need ClickHouse?
Fraud questions are geospatial and time-windowed (“was the phone near this restaurant in this window?”). ClickHouse stores live GPS and supports analytics that feed the agent—without dumping entire histories into the LLM.

### 5. Which sponsor integrations are actually live?
As of the 2026-10-09 health check: **AWS, OpenAI, ClickHouse, MongoDB, and ElevenLabs** all report `live`. Confirm anytime via public `GET /health`.

### 6. Are you freezing real bank accounts?
No. Freezes and transfers run on a **functional mock bank**. We never claim a real FI freeze or fund movement.

### 7. How do you prove the freeze worked?
After restriction, `POST /v1/bank/transfer` (or Demo Lab “Attempt transfer”) returns `success: false` and `status: rejected_restricted` while `restricted: true`.

### 8. What happens if GPS is missing or inaccurate?
Absence of GPS is **not** treated as proof of guilt. Restaurant cases can become **Needs review**; horizontal accuracy and match confidence matter. Users can confirm or freeze manually (Face ID for freeze).

### 9. Why doesn't a foreign transaction automatically mean fraud?
Online merchants often show foreign descriptors while the cardholder is at home. Our Colombia online path prefers **Needs review** over automatic freeze unless stronger takeover signals appear.

### 10. How is user location data protected?
Permissioned iOS capture, authenticated upload, tenant-scoped queries, user-controllable pause/delete paths, and no tying deletion to the AWS suspend deadline. Minimized derived evidence goes to the agent—not a raw full dump as a product goal.

### 11. What if the user's phone is stolen?
That’s a first-class scenario: new device + MFA/security changes + risky transfer → investigate → policy may freeze → attacker transfer blocked. Face ID on the owner’s device gates unfreeze. A thief with the unlocked phone is a residual risk we disclose; biometrics raise the bar for protection changes.

### 12. Can the AI mistakenly freeze an account?
The AI cannot freeze by itself. Policy must authorize. Residual false positives are possible in any heuristic system; consumers get **Needs review** paths and Face ID–gated unfreeze.

### 13. What does ElevenLabs actually do today?
**Live text-to-speech** generation for a disclosed AI fraud-hotline script after escalation. We do **not** claim a completed outbound PSTN call in this MVP.

### 14. Is the backend really running on AWS?
Yes. API Gateway → Lambda `sentinel-api` in `us-east-1`. Health reports `deployment_target: aws`. Localhost is for tests only, not the demo host.

### 15. What happens at the Sunday shutdown deadline?
EventBridge schedule `sentinel-sunday-suspend` at `2026-10-12T06:00:00Z` (Sun Oct 11, 2026 11:00 PM PT) invokes a controller that disables project ingress/compute paths. **No automatic deletion** of stacks, databases, GPS, secrets, or logs. Residual storage costs may continue. Resume/extend scripts exist.

### 16. What would be required to integrate a real financial institution?
Contractual API access, stronger auth/KYC, PCI and privacy reviews, irreversible-action dual control, audit pipelines, and replacing the mock bank adapter—without letting an LLM hold unilateral freeze authority.

### 17. What decisions are left to the AI versus deterministic code?
**AI:** evidence gathering via tools, natural-language conclusions, competing explanations. **Deterministic:** auth, tenant isolation, policy authorize/deny for restrict/unrestrict, mock-bank enforce/verify, consumer action routing, suspension controller behavior.
