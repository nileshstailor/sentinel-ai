"""Deterministic security policy — LLM cannot directly freeze accounts."""

from __future__ import annotations

from typing import Any

from app.models.schemas import AgentConclusion, ResponseLevel


class SecurityPolicyEngine:
    """Approves/denies protective actions independently of the LLM."""

    def decide(
        self,
        conclusion: AgentConclusion,
        *,
        user_policy: dict[str, Any],
        security_signals: list[str],
        channel: str | None = None,
    ) -> dict[str, Any]:
        level = conclusion.response_level
        if isinstance(level, int):
            try:
                level = ResponseLevel(level)
            except ValueError:
                level = ResponseLevel.REVIEW

        # Deterministic override: strong takeover bundles authorize restrict even if the
        # LLM under-escalates. The model cannot freeze accounts, but it also cannot
        # silently suppress a clear account-takeover signal set.
        if self._strong_takeover_bundle(security_signals) and user_policy.get(
            "auto_restrict_on_takeover", True
        ):
            if user_policy.get("allow_level3_restrict", True):
                return {
                    "approved": True,
                    "action": "restrict_account",
                    "response_level": ResponseLevel.RESTRICT.value,
                    "reason": "Deterministic takeover bundle (new device + MFA + recipient + transfer)",
                    "requires_verification": True,
                    "llm_response_level": int(level.value),
                }

        # Online Colombia alone must not freeze
        if user_policy.get("colombia_online_alone_is_not_fraud", True):
            if channel in {"card_not_present", "Channel.CARD_NOT_PRESENT"} and level.value >= 3:
                if not self._strong_takeover_bundle(security_signals):
                    return {
                        "approved": False,
                        "action": None,
                        "response_level": ResponseLevel.REVIEW.value,
                        "reason": "CNP/online foreign merchant alone cannot authorize restrict",
                    }

        if level.value >= ResponseLevel.RESTRICT.value:
            if not user_policy.get("allow_level3_restrict", True):
                return {
                    "approved": False,
                    "action": None,
                    "response_level": ResponseLevel.REVIEW.value,
                    "reason": "User policy disables automatic restrict",
                }
            if not user_policy.get("auto_restrict_on_takeover", True) and "takeover" in " ".join(
                security_signals
            ):
                return {
                    "approved": False,
                    "action": None,
                    "response_level": ResponseLevel.REVIEW.value,
                    "reason": "Auto-restrict disabled",
                }
            # Require either high score or strong signal bundle
            if conclusion.risk_score < 0.7 and not self._strong_takeover_bundle(security_signals):
                return {
                    "approved": False,
                    "action": None,
                    "response_level": ResponseLevel.REVIEW.value,
                    "reason": "Risk score / signals insufficient for restrict",
                }
            return {
                "approved": True,
                "action": "restrict_account",
                "response_level": ResponseLevel.RESTRICT.value,
                "reason": "Deterministic policy authorized temporary demo restriction",
                "requires_verification": True,
            }

        if level.value >= ResponseLevel.REVIEW.value:
            return {
                "approved": True,
                "action": "request_user_verification",
                "response_level": ResponseLevel.REVIEW.value,
                "reason": "Customer review warranted",
            }

        if level.value >= ResponseLevel.SILENT.value:
            return {
                "approved": True,
                "action": "silent_log",
                "response_level": ResponseLevel.SILENT.value,
                "reason": "Silent verification / digest",
            }

        return {
            "approved": True,
            "action": "allow",
            "response_level": ResponseLevel.ALLOW.value,
            "reason": "No protective action",
        }

    @staticmethod
    def _strong_takeover_bundle(signals: list[str]) -> bool:
        joined = " ".join(s.lower() for s in signals)
        needed = ["new_device", "mfa", "recipient", "transfer"]
        hits = sum(1 for n in needed if n in joined)
        return hits >= 3
