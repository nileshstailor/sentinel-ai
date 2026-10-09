# Sentinel AI — Implementation Status

**Updated:** 2026-10-09 (submission audit)  
**Suspend deadline:** 2026-10-11 23:00 America/Los_Angeles → `2026-10-12T06:00:00Z`  
**AWS account:** `284981582445` / `us-east-1`  
**Authorized spend:** $300 (advisory budget `SentinelAI-Hackathon-300` → nstailor87@gmail.com)

## Live AWS endpoints

| Item | Value |
|------|--------|
| API URL | `https://8m6o4go9oc.execute-api.us-east-1.amazonaws.com/prod/` |
| Lambda | `sentinel-api` |
| Suspend schedule | `sentinel-sunday-suspend` = `at(2026-10-12T06:00:00)` UTC **ENABLED** |
| Secrets | `sentinel-ai/hackathon` |

## Verified on AWS (2026-10-09)

| Check | Result |
|-------|--------|
| `GET /health` | ok; clickhouse/mongodb/openai/elevenlabs = **live**; maintenance_mode=false |
| GPS ingest | live ClickHouse path previously verified |
| Account takeover | restricted=true; subsequent transfer `rejected_restricted` |
| ElevenLabs SOS | success, `live_tts`, audio bytes returned |
| Suspension controller status | preserves_data=true; deletes_resources=false |
| Budget alerts | nstailor87@gmail.com @ 50/80/100% of $300 |

## iOS

- Info.plist / project.yml use **placeholder** API token for safe publishing  
- Local demo: Demo Lab Save & Sync, or gitignored `Config.local.plist`  
- Face ID on freeze / unfreeze / keep-frozen / hotline (not scenario launch)  
- Busy UI, result alerts, local urgent notifications  

## Real vs simulated

| Capability | Mode |
|------------|------|
| API hosting | LIVE AWS |
| GPS | LIVE device → API → ClickHouse |
| OpenAI / Mongo / ClickHouse / ElevenLabs TTS | LIVE |
| Bank / transfers / freezes | Functional MOCK bank |

## Submission package

See `submission/` and root `README.md`. GitHub push and demo video require owner action.
