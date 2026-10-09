"""ElevenLabs emergency fraud SOS (stretch).

Makes a LIVE ElevenLabs TTS API call. The agent discloses it is AI,
then explains the freeze and requests fraud-hotline logging.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah — reassuring demo voice

HOTLINE_SCRIPT = (
    "Hello. This is Sentinel AI, an artificial intelligence fraud assistant. "
    "I am not a human, and I am not the account holder. "
    "We detected a high-confidence account takeover: a new device was registered, "
    "MFA was changed, and an unauthorized transfer was attempted. "
    "A temporary protective restriction is now on the account. "
    "Please log this escalation and keep the freeze in place until the customer verifies. "
    "Thank you."
)


class ElevenLabsSOS:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.mode = "live" if self.settings.elevenlabs_api_key else "unavailable"
        self.voice_id = self.settings.elevenlabs_voice_id or DEFAULT_VOICE_ID

    def escalate(
        self,
        *,
        incident_id: str,
        user_id: str,
        reason: str,
    ) -> dict[str, Any]:
        if self.mode != "live":
            return {
                "success": False,
                "mode": "unavailable",
                "message": "ELEVENLABS_API_KEY not configured",
            }

        audio_bytes, meta = self._synthesize(HOTLINE_SCRIPT)
        result: dict[str, Any] = {
            "success": bool(audio_bytes),
            "mode": "live_tts",
            "provider": "elevenlabs",
            "voice_id": self.voice_id,
            "incident_id": incident_id,
            "user_id": user_id,
            "reason": reason,
            "disclosed_ai_assistant": True,
            "script": HOTLINE_SCRIPT,
            "audio_bytes": len(audio_bytes or b""),
            "content_type": meta.get("content_type"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "summary": (
                "Live ElevenLabs TTS for an AI fraud-hotline escalation after an account freeze."
            ),
            "telephony": "not_configured",
        }

        phone = (self.settings.elevenlabs_agent_phone or "").strip()
        if phone and audio_bytes:
            result["telephony"] = "configured_but_outbound_not_enabled_in_mvp"
            result["mock_hotline_ref"] = phone
            result["note"] = (
                "Phone number present; MVP verifies live TTS. "
                "Outbound PSTN requires ElevenLabs Agents telephony setup."
            )

        return result

    def _synthesize(self, text: str) -> tuple[bytes | None, dict[str, Any]]:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.7},
        }
        try:
            with httpx.Client(timeout=45.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    logger.warning("ElevenLabs TTS failed: %s %s", resp.status_code, resp.text[:300])
                    return None, {"error": resp.text[:300], "status_code": resp.status_code}
                return resp.content, {"content_type": resp.headers.get("content-type", "audio/mpeg")}
        except Exception as exc:  # noqa: BLE001
            logger.warning("ElevenLabs TTS exception: %s", exc)
            return None, {"error": str(exc)}


_client: ElevenLabsSOS | None = None


def get_elevenlabs_sos() -> ElevenLabsSOS:
    global _client
    if _client is None:
        _client = ElevenLabsSOS()
    return _client


def reset_elevenlabs_for_tests() -> ElevenLabsSOS:
    global _client
    _client = ElevenLabsSOS(Settings(elevenlabs_api_key=""))
    return _client
