# Sentinel AI architecture

This document reflects the **deployed** hackathon MVP (AWS `us-east-1`, API Gateway → Lambda FastAPI), not an aspirational redesign.

## System diagram

```mermaid
flowchart LR
  subgraph Device["iPhone · SwiftUI"]
    UI[Home / Alerts / Demo Lab]
    GPS[Core Location]
    BIO[Face ID]
    UN[Local notifications]
  end

  subgraph AWS["AWS us-east-1"]
    APIGW[API Gateway prod]
    LAMBDA[Lambda sentinel-api<br/>FastAPI + Mangum]
    SM[Secrets Manager<br/>sentinel-ai/hackathon]
    SCH[EventBridge Scheduler<br/>sentinel-sunday-suspend]
    CTRL[Suspension controller Lambda]
  end

  subgraph Sponsors["Sponsor services"]
    OA[OpenAI<br/>tool-calling investigator]
    CH[ClickHouse Cloud<br/>GPS + events]
    MG[MongoDB Atlas<br/>incidents + mock bank]
    EL[ElevenLabs<br/>live TTS]
  end

  subgraph Bank["Functional mock bank"]
    MB[(Account state<br/>restrict / transfer)]
  end

  UI --> APIGW
  GPS -->|POST /v1/gps| APIGW
  BIO -.->|gates freeze/unfreeze/hotline| UI
  UN -.-> UI
  APIGW --> LAMBDA
  LAMBDA --> SM
  LAMBDA --> OA
  LAMBDA --> CH
  LAMBDA --> MG
  LAMBDA --> MB
  LAMBDA --> EL
  SCH -->|at 2026-10-12T06:00:00Z| CTRL
  CTRL -.->|disable ingress/concurrency<br/>no deletes| LAMBDA
```

## Autonomous execution flow

```mermaid
sequenceDiagram
  participant App as iPhone App
  participant API as API Gateway / Lambda
  participant Agent as OpenAI Investigator
  participant CH as ClickHouse
  participant Policy as SecurityPolicyEngine
  participant Bank as Mock Bank
  participant DB as MongoDB

  App->>API: Ingest event / Demo scenario
  API->>CH: Query GPS / related events
  API->>Agent: Investigate with tools
  Agent->>API: Tool calls (txns, GPS match, security events, …)
  API->>CH: Analytics reads
  API->>DB: Context / policy / devices
  Agent-->>API: Structured conclusion + evidence refs
  API->>Policy: Evaluate response level / actions
  alt Policy authorizes restrict
    Policy->>Bank: restrict(account)
    Bank-->>Policy: restricted=true
    Policy->>Bank: verify state
  end
  API->>DB: Persist incident + actions
  API-->>App: Incident (Verified / Needs review / Account protected)
  App->>App: Local urgent notification (when applicable)
  Note over App,Bank: Prove freeze: POST /v1/bank/transfer → rejected_restricted
```

## Trust boundaries

| Boundary | Rule in this MVP |
|----------|------------------|
| **LLM → bank** | OpenAI may *recommend* protection. It cannot call mock-bank restrict APIs directly. |
| **Policy → bank** | `SecurityPolicyEngine` (deterministic) must authorize restrict/unrestrict. |
| **Device → API** | Bearer token + `X-Sentinel-User`. Hackathon auth, not Cognito. |
| **User → freeze UI** | Face ID / biometrics required for freeze, unfreeze, keep-frozen, and hotline TTS. |
| **Public incident API** | Consumer fields only; raw `tool_trace` is stripped from client responses. |
| **Suspension controller** | Can disable project ingress/compute; **cannot** delete stacks, DBs, GPS, or secrets. Independent of `sentinel-api` concurrency. |

## Component map (as deployed)

| Component | Implementation |
|-----------|----------------|
| Mobile | `ios/SentinelAI` SwiftUI |
| API | `backend/app` on Lambda `sentinel-api` |
| Agent | `backend/app/agents` + `integrations/openai_client.py` |
| Mock bank | `backend/app/simulation/mock_bank.py` |
| Scenarios | `backend/app/simulation/scenarios.py` |
| Infra | `infrastructure/cdk` (`SentinelAI-Api`, `SentinelAI-Suspension`) |

## Live vs simulated (architecture view)

```mermaid
flowchart TB
  subgraph Real["Real in deployed demo"]
    R1[iPhone GPS]
    R2[AWS hosting]
    R3[OpenAI API]
    R4[ClickHouse]
    R5[MongoDB]
    R6[ElevenLabs TTS]
  end
  subgraph Sim["Simulated by design"]
    S1[Bank accounts]
    S2[Transfers]
    S3[Account freezes]
  end
```

## Related docs

- Residual suspend costs: [`aws-suspension-and-costs.md`](aws-suspension-and-costs.md)
- Security notes: [`security.md`](security.md)
- Submission package: [`../submission/FINAL_SUBMISSION.md`](../submission/FINAL_SUBMISSION.md)
