# Final submission manifest — Sentinel AI

| Field | Value |
|-------|--------|
| **Project title** | Sentinel AI |
| **Tagline** | Your Money Has a Bodyguard. |
| **Official event** | [Tokens& Cyberdefense Hackathon](https://tokensand.com/cyberhack) |
| **Submission deadline** | October 9, 2026, 4:30 PM Pacific |
| **Repository URL** | https://github.com/nileshstailor/sentinel-ai |
| **Demo video URL** | Local: `submission/pitch-assets/demo.mp4` · Deck: `submission/PITCH_DECK.html` · _Add public share link when uploaded_ |
| **Architecture** | [`docs/architecture.md`](../docs/architecture.md) |
| **Project description** | [`PROJECT_DESCRIPTION.md`](PROJECT_DESCRIPTION.md) |
| **Judge Q&A** | [`JUDGE_QA.md`](JUDGE_QA.md) |

## Sponsor technologies

AWS · OpenAI · ClickHouse · MongoDB · ElevenLabs

## Team details

| Name | Role | Email |
|------|------|-------|
| _TBD_ | _TBD_ | _TBD_ |

Confirm before form submit. Do not invent.

## Live deployment status (verified 2026-10-09)

| Check | Result |
|-------|--------|
| API health | `ok: true`, `deployment_target: aws` |
| Maintenance | `false` |
| Suspend at | `2026-10-12T06:00:00Z` |
| clickhouse | live |
| mongodb | live |
| openai | live |
| elevenlabs | live |
| Scheduler `sentinel-sunday-suspend` | ENABLED `at(2026-10-12T06:00:00)` |
| Takeover → freeze | verified |
| Transfer probe | `rejected_restricted` |
| ElevenLabs SOS | success, live_tts |

Public health URL:  
`https://8m6o4go9oc.execute-api.us-east-1.amazonaws.com/prod/health`

## Real vs simulated (summary)

- **Real:** iPhone GPS, AWS hosting, OpenAI investigation, ClickHouse, MongoDB, ElevenLabs TTS, policy + verification workflow  
- **Simulated:** bank accounts, transfers, freezes (functional mock bank)  
- **Not deployed:** completed outbound PSTN fraud-hotline call  

## Submission readiness status

| Area | Status |
|------|--------|
| Product demo path | Ready on AWS + iOS |
| Documentation package | Ready in-repo |
| Secret hygiene for publish | Placeholders applied; publish only after git push review |
| GitHub URL | Blocked on your approval |
| Demo video | Blocked on your recording |
| Official form | Blocked on you |

## Discrepancies vs older checklists

- `IMPLEMENTATION_STATUS.md` previously listed Mongo/ElevenLabs as still needed; **health and live probes now show both live**.  
- `docs/aws-suspension-verification.md` still contains older “BLOCKED — not deployed” rows; **schedule read-back and controller status are live** (see `scripts/aws-status.sh`). Prefer live AWS read-back over stale checklist cells.  
- Face ID gates **freeze/unfreeze/hotline**, not Demo Lab scenario launch.  
- Public incidents omit `tool_trace` by design.
