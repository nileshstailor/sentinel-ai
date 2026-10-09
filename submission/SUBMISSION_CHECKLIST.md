# Official submission checklist — Sentinel AI

Only check an item when verified. Last audit: **2026-10-09**.

## Repository & secrets

- [x] GitHub repository accessible to judges (public: https://github.com/nileshstailor/sentinel-ai)
- [x] Secrets scrubbed from iOS `Info.plist` / `project.yml` (placeholders)
- [x] `.gitignore` excludes `.env`, local config, recordings
- [x] `.env.example` present (no live secrets)
- [x] Git repository initialized and pushed
- [x] Confirmed no live tokens in public tree after push (`.env` absent; APIToken placeholder)

## Documentation

- [x] README complete (`README.md`)
- [x] Architecture diagram complete (`docs/architecture.md`)
- [x] Project description complete (`submission/PROJECT_DESCRIPTION.md`)
- [x] Judge Q&A complete (`submission/JUDGE_QA.md`)
- [x] Demo script / shot list / recording checklist complete
- [x] Sponsor integrations accurately documented (live as of health check)
- [ ] Team names and contact emails confirmed *(do not invent)*

## Live system

- [x] Actual AWS API responding (`/health` ok)
- [x] Integrations report live: clickhouse, mongodb, openai, elevenlabs
- [x] `maintenance_mode` false
- [x] Mock-bank freeze test passed (account_takeover → restricted)
- [x] Follow-up transfer rejection verified (`rejected_restricted`)
- [x] ElevenLabs TTS returns success + audio bytes
- [x] Demo scenarios operational on AWS
- [x] Suspend schedule ENABLED `at(2026-10-12T06:00:00)` UTC

## Video & form

- [ ] Demo video recorded
- [ ] Demo video uploaded and shareable
- [ ] Video URL pasted into `FINAL_SUBMISSION.md`
- [ ] Official hackathon form submitted ([tokensand.com/cyberhack](https://tokensand.com/cyberhack))

## AWS safety (do not destroy)

- [x] No teardown performed during submission prep
- [x] Suspension is schedule-based and reversible (controller preserves data)
- [x] Residual cost disclosure available (`docs/aws-suspension-and-costs.md`)

---

### Blockers for a complete submit today

1. **You** must approve GitHub create/push (repo was not initialized before this prep).  
2. **You** must record/upload the demo video.  
3. **You** must fill team names/emails.  
4. **You** must complete the official event form before **4:30 PM Pacific, Oct 9, 2026**.
