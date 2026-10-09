"""Plain-language consumer copy — no IDs, no “call your bank” chores."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def friendly_title(scenario: str | None, fallback: str = "Activity alert") -> str:
    mapping = {
        "a_restaurant_match": "Restaurant charge verified",
        "a_restaurant_insufficient": "Restaurant charge needs a look",
        "b_colombia_online": "International online purchase",
        "b_colombia_card_present": "Unusual card activity abroad",
        "c_account_takeover": "Suspicious sign-in and transfer blocked",
    }
    if scenario and scenario.lower() in mapping:
        return mapping[scenario.lower()]
    return _title_case_safe(fallback)


def build_customer_copy(
    *,
    scenario: str | None,
    response_level: int,
    decision_action: str | None,
    restricted: bool,
    tool_trace: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return consumer fields with proper grammar and actionable choices."""
    scenario_key = (scenario or "").lower()
    findings = explain_findings(tool_trace or [], scenario_key)
    gps_nearby = _gps_nearby_from_trace(tool_trace or [])

    if decision_action == "restrict_account" or restricted or scenario_key.startswith("c_"):
        return {
            "customer_status": "Account protected",
            "customer_summary": (
                "Sentinel spotted signs of an account takeover—like a new device, "
                "security setting changes, and a risky transfer—so your demo account "
                "was frozen to stop further transfers."
            ),
            "customer_findings": findings
            or [
                "A new or unrecognized device tried to use your account.",
                "Security settings were changed recently.",
                "A high-risk transfer was attempted.",
            ],
            "available_actions": [
                {"id": "keep_frozen", "label": "Keep account frozen"},
                {"id": "unfreeze", "label": "Unfreeze my account"},
            ],
            "severity": "critical",
            "status": "restricted",
            "title": friendly_title(scenario_key),
        }

    # Restaurant / delayed charges: classify from real GPS proximity evidence.
    if scenario_key.startswith("a_restaurant") or "restaurant" in scenario_key:
        merchant = _merchant_from_trace(tool_trace or []) or "the restaurant"
        if gps_nearby is True or (gps_nearby is None and ("match" in scenario_key or response_level <= 1)):
            return {
                "customer_status": "Verified",
                "customer_summary": (
                    f"This delayed charge from {merchant} lines up with your location near the restaurant "
                    "around the time of the purchase. Restaurant bills often post a few days later, "
                    "so Sentinel marked it as verified."
                ),
                "customer_findings": findings
                or [
                    f"Your phone was near {merchant} around purchase time.",
                    "The charge amount looks like a normal restaurant bill.",
                ],
                "available_actions": [
                    {"id": "dismiss", "label": "Looks good"},
                ],
                "severity": "info",
                "status": "verified",
                "title": "Restaurant charge verified",
            }

        # gps_nearby is False (or insufficient scenario with no match)
        return {
            "customer_status": "Needs review",
            "customer_summary": (
                f"This delayed charge from {merchant} posted later than usual, and Sentinel did not find "
                "GPS history close to that restaurant for the purchase window. Missing location data is not "
                "proof of fraud—you can confirm it with one tap."
            ),
            "customer_findings": findings
            or [
                f"No GPS points were close to {merchant} during the purchase window.",
                "No matching travel plan was saved for San Francisco on that date.",
            ],
            "available_actions": [
                {"id": "confirm_ok", "label": "This is fine"},
                {"id": "freeze", "label": "Freeze my account"},
            ],
            "severity": "medium",
            "status": "needs_review",
            "title": "Restaurant charge needs a look",
        }

    if scenario_key.startswith("b_colombia_online") or (
        "colombia" in scenario_key and "online" in scenario_key
    ):
        return {
            "customer_status": "Needs review",
            "customer_summary": (
                "Your phone was in San Francisco while an online purchase showed a Colombia-linked merchant. "
                "Online orders often show a foreign merchant location even when you shop from home, "
                "so this alone is not enough to freeze your account."
            ),
            "customer_findings": findings
            or [
                "Phone location was in San Francisco near the time of the purchase.",
                "Charge was online (card-not-present), not a swipe in Colombia.",
                "No takeover signals like a new device plus password reset.",
            ],
            "available_actions": [
                {"id": "confirm_ok", "label": "This is fine"},
                {"id": "freeze", "label": "Freeze my account"},
            ],
            "severity": "medium",
            "status": "needs_review",
            "title": friendly_title("b_colombia_online"),
        }

    if response_level >= 3 or decision_action == "restrict_account":
        return {
            "customer_status": "Account protected",
            "customer_summary": (
                "Sentinel found several high-risk signals together and froze your demo account "
                "to block further transfers."
            ),
            "customer_findings": findings
            or ["Multiple high-risk signals appeared close together."],
            "available_actions": [
                {"id": "keep_frozen", "label": "Keep account frozen"},
                {"id": "unfreeze", "label": "Unfreeze my account"},
            ],
            "severity": "high",
            "status": "restricted",
            "title": friendly_title(scenario_key, "Account protected"),
        }

    if decision_action == "request_user_verification" or response_level == 2:
        return {
            "customer_status": "Needs review",
            "customer_summary": (
                "Something about this activity looked unusual. Review the details below and choose "
                "whether everything looks fine or you want to freeze the demo account."
            ),
            "customer_findings": findings
            or ["Activity did not fully match your usual pattern."],
            "available_actions": [
                {"id": "confirm_ok", "label": "This is fine"},
                {"id": "freeze", "label": "Freeze my account"},
            ],
            "severity": "medium",
            "status": "needs_review",
            "title": friendly_title(scenario_key, "Activity needs a look"),
        }

    return {
        "customer_status": "Verified",
        "customer_summary": "Sentinel checked this activity and did not find a reason to alert you.",
        "customer_findings": findings or ["No high-risk signals found."],
        "available_actions": [{"id": "dismiss", "label": "Looks good"}],
        "severity": "info",
        "status": "verified",
        "title": friendly_title(scenario_key, "Activity verified"),
    }


def _gps_nearby_from_trace(tool_trace: list[dict[str, Any]]) -> bool | None:
    """True if merchant match found nearby GPS; False if match ran with 0 hits; None if unknown."""
    saw_match_tool = False
    for item in tool_trace:
        if item.get("tool") != "match_merchant_to_visits":
            continue
        saw_match_tool = True
        result = item.get("result") or {}
        if isinstance(result, dict) and int(result.get("match_count") or 0) > 0:
            return True
    if saw_match_tool:
        return False
    return None


def _merchant_from_trace(tool_trace: list[dict[str, Any]]) -> str:
    for item in tool_trace:
        if item.get("tool") != "get_transaction_details":
            continue
        result = item.get("result") or {}
        if isinstance(result, dict) and result.get("merchant"):
            return str(result["merchant"])
    return ""


def explain_findings(tool_trace: list[dict[str, Any]], scenario: str) -> list[str]:
    """Turn tool results into human-readable bullets (no IDs)."""
    findings: list[str] = []
    match_count = 0
    travel_plans = 0
    security_types: list[str] = []
    channel = ""
    merchant = ""

    for item in tool_trace:
        tool = item.get("tool")
        result = item.get("result") or {}
        if not isinstance(result, dict):
            continue
        if tool == "match_merchant_to_visits":
            match_count = int(result.get("match_count") or 0)
            considered = int(result.get("gps_points_considered") or 0)
            if match_count > 0:
                findings.append(
                    "Your location history shows you were near the restaurant around purchase time."
                )
            elif considered == 0:
                findings.append("No GPS points were available in that purchase time window.")
            else:
                findings.append(
                    "No GPS points were close enough to the restaurant during the purchase window. "
                    "Missing GPS is not proof you were never there."
                )
        elif tool == "get_travel_context":
            plans = result.get("plans") or []
            travel_plans = len(plans) if isinstance(plans, list) else 0
            if travel_plans == 0:
                findings.append("No travel plans were saved for this trip.")
            else:
                findings.append(
                    f"You have {travel_plans} travel plan{'s' if travel_plans != 1 else ''} on file."
                )
        elif tool == "get_security_events":
            events = result.get("events") or []
            if isinstance(events, list):
                for e in events:
                    if isinstance(e, dict) and e.get("event_type"):
                        security_types.append(str(e["event_type"]))
        elif tool == "get_transaction_details":
            channel = str(result.get("channel") or "")
            merchant = str(result.get("merchant") or "")

    if channel in {"card_not_present", "Channel.CARD_NOT_PRESENT"}:
        findings.append("This was an online (card-not-present) purchase, not an in-person swipe.")
    elif channel in {"card_present", "Channel.CARD_PRESENT"}:
        findings.append("This was recorded as an in-person card purchase.")

    nice_security = {
        "new_device": "A new device signed in",
        "mfa_change": "Multi-factor authentication settings were changed",
        "new_recipient": "A new transfer recipient was added",
        "failed_login": "There were failed sign-in attempts",
        "transfer": "A transfer was attempted",
    }
    for raw in security_types:
        label = nice_security.get(raw)
        if label and label not in findings:
            findings.append(label + ".")

    if merchant and match_count > 0:
        findings.insert(0, f"Charge appears related to {merchant}.")
    elif merchant and "restaurant" in scenario and match_count == 0:
        findings.insert(0, f"Charge appears related to {merchant}.")

    out: list[str] = []
    seen: set[str] = set()
    for f in findings:
        text = _sentence(f)
        if text not in seen:
            seen.add(text)
            out.append(text)
    return out[:8]


def alert_subtitle(created_at: datetime | None) -> str:
    if not created_at:
        return "Recent alert"
    try:
        return "Alert from " + created_at.strftime("%b %d, %Y · %I:%M %p").replace(" 0", " ")
    except Exception:
        return "Recent alert"


def _sentence(text: str) -> str:
    text = " ".join(str(text).split()).strip()
    if not text:
        return text
    if text[-1] not in ".!?":
        text += "."
    return text[0].upper() + text[1:]


def _title_case_safe(text: str) -> str:
    text = " ".join(str(text).split()).strip()
    if not text:
        return "Activity alert"
    return text[0].upper() + text[1:]
