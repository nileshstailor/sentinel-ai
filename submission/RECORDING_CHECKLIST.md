# Recording checklist — Sentinel AI demo video

Record authentic footage only. Do not fabricate API successes.

## Before recording

- [ ] iPhone unlocked; Xcode build of current Sentinel AI installed
- [ ] Demo Lab **Save & Sync** succeeds against AWS (not localhost)
- [ ] Notifications allowed (optional but nice for takeover)
- [ ] Location allowed; recent GPS visible in Location tab
- [ ] Face ID / passcode ready for freeze/unfreeze/hotline
- [ ] `GET .../prod/health` shows all four integrations `live`, `maintenance_mode: false`
- [ ] Demo Lab **Reset alerts & unfreeze** completed
- [ ] Quiet room; mic test; screen recording permissions on
- [ ] Token fields not visible on camera (or covered)

## During recording (~90s)

- [ ] 0–15s Home intro
- [ ] 15–30s Location / GPS
- [ ] 30–55s Stolen phone → Account protected → Attempt transfer → blocked
- [ ] 55–70s Restaurant Verified and/or Needs review
- [ ] 70–80s ElevenLabs TTS success (no PSTN claim)
- [ ] 80–90s Close with sponsors + mock-bank honesty

## After recording

- [ ] Review: freeze proof clearly readable (`rejected_restricted` / Transfer blocked)
- [ ] No secrets visible in frames
- [ ] Export 1080p (or device native); keep master offline
- [ ] Upload unlisted/public-as-required by hackathon form
- [ ] Paste share URL into `FINAL_SUBMISSION.md` and submission form
- [ ] Store local copy under `submission/recordings/` (gitignored)

## If something fails mid-take

| Failure | Fix | Re-record from |
|---------|-----|----------------|
| Account already frozen | Reset Demo Lab | Takeover segment |
| Transfer not blocked | Run Stolen phone first | Prove restriction |
| ElevenLabs fail | Retry once; check health `elevenlabs=live` | Hotline segment only |
| GPS empty | Open Location, wait for fix, sync | GPS segment |
| Auth / hostname error | Save & Sync correct AWS URL + token | Entire take |

## Automation note

No reliable headless iPhone screen-recording automation is configured in this repo. **You must record on-device** (or QuickTime iPhone screen share on macOS).
