"""Typed tool implementations for the fraud investigator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.integrations.clickhouse_client import ClickHouseStore
from app.integrations.mongodb_client import MongoStore
from app.simulation.mock_bank import MockBankService


@dataclass
class ToolContext:
    user_id: str
    incident_id: str
    account_id: str
    ch: ClickHouseStore
    mongo: MongoStore
    bank: MockBankService
    pending_protection: dict[str, Any] = field(default_factory=dict)


def execute_tool(name: str, args: dict[str, Any], ctx: ToolContext) -> Any:
    handlers = {
        "get_transaction_details": _get_transaction_details,
        "query_location_history": _query_location_history,
        "match_merchant_to_visits": _match_merchant_to_visits,
        "get_travel_context": _get_travel_context,
        "get_security_events": _get_security_events,
        "get_trusted_devices": _get_trusted_devices,
        "get_policy": _get_policy,
        "get_related_activity": _get_related_activity,
        "request_user_verification": _request_user_verification,
        "request_protection": _request_protection,
        "check_protection_status": _check_protection_status,
        "escalate_fraud_incident": _escalate_fraud_incident,
        "record_investigation": _record_investigation,
    }
    handler = handlers.get(name)
    if not handler:
        return {"error": f"Unknown tool {name}"}
    return handler(args, ctx)


def _get_transaction_details(args: dict[str, Any], ctx: ToolContext) -> Any:
    rows = ctx.ch.get_financial(ctx.user_id, event_id=args.get("event_id"))
    if not rows:
        return {"error": "not_found", "event_id": args.get("event_id")}
    e = rows[0]
    return e.model_dump(mode="json")


def _query_location_history(args: dict[str, Any], ctx: ToolContext) -> Any:
    start = _parse(args.get("start_iso"))
    end = _parse(args.get("end_iso"))
    limit = int(args.get("limit") or 20)
    rows = ctx.ch.query_gps(ctx.user_id, start=start, end=end, limit=min(limit, 50))
    # Minimized evidence — do not dump full history to the model
    return {
        "count": len(rows),
        "points": [
            {
                "event_id": r.event_id,
                "event_timestamp": r.event_timestamp.isoformat(),
                "lat": round(r.lat, 5),
                "lon": round(r.lon, 5),
                "horizontal_accuracy_m": r.horizontal_accuracy_m,
                "synthetic": r.synthetic,
            }
            for r in rows
        ],
        "caveat": "Absence of a point does not prove non-presence.",
    }


def _match_merchant_to_visits(args: dict[str, Any], ctx: ToolContext) -> Any:
    around = _parse(args.get("around_iso")) or datetime.now(timezone.utc)
    return ctx.ch.match_merchant_visits(
        ctx.user_id,
        float(args["merchant_lat"]),
        float(args["merchant_lon"]),
        around=around,
        lookback_days=int(args.get("lookback_days") or 14),
    )


def _get_travel_context(_args: dict[str, Any], ctx: ToolContext) -> Any:
    plans = ctx.mongo.list_travel(ctx.user_id)
    return {"plans": [p.model_dump(mode="json") for p in plans]}


def _get_security_events(args: dict[str, Any], ctx: ToolContext) -> Any:
    hours = int(args.get("hours") or 72)
    events = ctx.ch.get_security(ctx.user_id, hours=hours)
    return {"events": [e.model_dump(mode="json") for e in events]}


def _get_trusted_devices(_args: dict[str, Any], ctx: ToolContext) -> Any:
    devices = ctx.mongo.list_devices(ctx.user_id)
    return {"devices": [d.model_dump(mode="json") for d in devices]}


def _get_policy(_args: dict[str, Any], ctx: ToolContext) -> Any:
    return ctx.mongo.get_policy(ctx.user_id)


def _get_related_activity(args: dict[str, Any], ctx: ToolContext) -> Any:
    all_fin = ctx.ch.get_financial(ctx.user_id)
    return {
        "events": [e.model_dump(mode="json") for e in all_fin[:15]],
        "focus_event_id": args.get("event_id"),
    }


def _request_user_verification(args: dict[str, Any], ctx: ToolContext) -> Any:
    return {
        "queued": True,
        "reason": args.get("reason"),
        "incident_id": ctx.incident_id,
        "note": "Verification request recorded; not a bank freeze.",
    }


def _request_protection(args: dict[str, Any], ctx: ToolContext) -> Any:
    ctx.pending_protection.update(args)
    return {
        "accepted_for_policy_review": True,
        "action_type": args.get("action_type"),
        "rationale": args.get("rationale"),
        "note": "LLM cannot execute freezes; deterministic policy must approve.",
    }


def _check_protection_status(args: dict[str, Any], ctx: ToolContext) -> Any:
    return ctx.bank.get_status(args.get("account_id") or ctx.account_id)


def _escalate_fraud_incident(args: dict[str, Any], ctx: ToolContext) -> Any:
    from app.integrations.elevenlabs_client import get_elevenlabs_sos

    sos = get_elevenlabs_sos().escalate(
        incident_id=ctx.incident_id,
        user_id=ctx.user_id,
        reason=str(args.get("reason") or "agent escalation"),
    )
    return {
        "escalated": bool(sos.get("success")),
        "reason": args.get("reason"),
        "incident_id": ctx.incident_id,
        "elevenlabs": sos,
    }


def _record_investigation(args: dict[str, Any], ctx: ToolContext) -> Any:
    return {"recorded": True, "incident_id": ctx.incident_id, **args}


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
