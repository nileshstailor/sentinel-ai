# Demo script — Sentinel AI (~90 seconds)

**Record on a real iPhone** with the live AWS API. Reset Demo Lab first if the account is already frozen. Allow Location + Notifications beforehand. Do **not** claim a completed outbound phone call for ElevenLabs.

---

## 90-second script (narration ↔ screen)

### 0:00–0:15 — Introduction
**Show:** Home tab, brand “SENTINEL AI”, protection On.  
**Say:**  
“This is Sentinel AI—your money has a bodyguard. Account takeovers move fast. We built an autonomous agent on iPhone and AWS that investigates risky activity and can freeze a mock bank account before the next transfer lands.”

### 0:15–0:30 — Real GPS intelligence
**Show:** Location tab → permission / recent coordinates updating → mention backend sync.  
**Say:**  
“First, real GPS. The phone captures Core Location and uploads points to our AWS API into ClickHouse—so investigations can ask where the body actually was, not just where a merchant label claims.”

### 0:30–0:55 — Account takeover + prove freeze *(hero moment)*
**Show:** Demo Lab → **Reset** (if needed) → **Stolen phone — Freeze account** → Alerts → **Account protected**.  
Then **Attempt transfer after takeover** → alert: Transfer blocked / rejected.  
**Say:**  
“Stolen phone scenario: new device, MFA change, risky transfer. OpenAI investigates with tools; policy authorizes a freeze. Account protected. Now we attempt another transfer—and the mock bank returns rejected_restricted. That’s the proof the freeze actually works.”

### 0:55–1:10 — Restaurant verification
**Show:** Reset (optional if freeze blocks nuance) → **Restaurant charge — Should Verify** and/or **Needs Review** → Alerts statuses.  
**Say:**  
“Restaurant bills post late. If GPS was near the restaurant, Sentinel can mark Verified. If evidence is thin, Needs review—without treating every delayed charge as a crisis.”

### 1:10–1:20 — ElevenLabs
**Show:** **Generate AI hotline voice** → Face ID → success alert.  
**Say:**  
“Stretch: live ElevenLabs text-to-speech—the voice an AI assistant would use to escalate a freeze to a fraud hotline. We’re generating that audio live; we’re not claiming a completed carrier phone call in this MVP.”

### 1:20–1:30 — Close
**Show:** Home with integrations or health mental checklist; freeze badge if still protected.  
**Say:**  
“Sponsors in the loop: AWS, OpenAI, ClickHouse, MongoDB, ElevenLabs. The bank layer is a functional simulation—GPS, cloud, and investigation are real. Sentinel AI: your money has a bodyguard.”

---

## 60-second alternate (if long)

| Time | Action | Line |
|------|--------|------|
| 0–10 | Home | “Sentinel AI—autonomous fraud bodyguard on iPhone + AWS.” |
| 10–20 | Location | “Real GPS into ClickHouse.” |
| 20–40 | Takeover + transfer | “Investigate, freeze, prove with rejected_restricted.” |
| 40–50 | Restaurant or Alerts | “Verified vs Needs review cuts false panic.” |
| 50–60 | ElevenLabs + close | “Live ElevenLabs hotline TTS. Mock bank, real agent.” |

---

## Recording tips

1. Airplane mode **off**; strong Wi-Fi/LTE.  
2. Demo Lab → Reset before takeover for a clean arc.  
3. Face ID ready for freeze/unfreeze/hotline only (scenarios do not require Face ID).  
4. Do not scroll past API token fields on camera; blur Demo Lab token if visible.  
5. Prefer screen recording + voiceover in one take; cut only if a network retry is needed.  
6. Upload privately (unlisted) and paste URL into `FINAL_SUBMISSION.md` after you have the link.
