"""FastAPI routes for Sentinel AI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agents.investigator import FraudInvestigatorService
from app.api.deps import require_auth
from app.config import get_settings
from app.integrations.clickhouse_client import get_clickhouse_store
from app.integrations.elevenlabs_client import get_elevenlabs_sos
from app.integrations.mongodb_client import get_mongo_store
from app.integrations.openai_client import get_openai_investigator
from app.models.schemas import (
    Channel,
    FinancialEvent,
    GpsEvent,
    HomeSummary,
    MockTransferRequest,
    SecurityEvent,
    TravelPlan,
)
from app.simulation.mock_bank import MockBankService
from app.simulation.scenarios import ScenarioRunner

router = APIRouter()


class GpsIngestRequest(BaseModel):
    lat: float
    lon: float
    horizontal_accuracy_m: float = 25.0
    event_timestamp: datetime | None = None
    source: str = "core_location"
    synthetic: bool = False


class FinancialIngestRequest(BaseModel):
    account_id: str = MockBankService.DEMO_ACCOUNT_ID
    channel: Channel
    merchant: str
    amount: float
    merchant_lat: float | None = None
    merchant_lon: float | None = None
    merchant_geo_confidence: float = 0.0
    authorization_time: datetime | None = None
    posting_time: datetime | None = None
    transaction_type: str = "purchase"
    metadata: dict[str, Any] = Field(default_factory=dict)
    auto_investigate: bool = True


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    ch = get_clickhouse_store()
    mongo = get_mongo_store()
    oi = get_openai_investigator()
    el = get_elevenlabs_sos()
    return {
        "ok": True,
        "service": "sentinel-ai",
        "maintenance_mode": settings.sentinel_maintenance_mode,
        "suspend_at_utc": settings.sentinel_suspend_at_utc,
        "integrations": {
            "clickhouse": ch.mode,
            "mongodb": mongo.mode,
            "openai": oi.mode,
            "elevenlabs": el.mode,
        },
        "deployment_target": "aws",
    }


@router.get("/v1/system/status")
def system_status() -> dict:
    settings = get_settings()
    return {
        "maintenance_mode": settings.sentinel_maintenance_mode,
        "suspend_at_utc": settings.sentinel_suspend_at_utc,
        "stack_name": settings.sentinel_stack_name,
        "region": settings.aws_region,
        "account_id": settings.aws_account_id,
    }


@router.get("/v1/home", response_model=HomeSummary)
def home(auth: dict = Depends(require_auth)) -> HomeSummary:
    settings = get_settings()
    ch = get_clickhouse_store()
    mongo = get_mongo_store()
    bank = MockBankService(mongo)
    bank.seed(auth["user_id"])
    status = bank.get_status(MockBankService.DEMO_ACCOUNT_ID)
    incidents = mongo.list_incidents(auth["user_id"])
    verified = [i for i in incidents if i.customer_status == "Verified" or i.status == "verified"]
    needs = [i for i in incidents if i.customer_status == "Needs review" or i.status == "needs_review"]
    frozen = [
        i
        for i in incidents
        if i.customer_status == "Account protected" or i.status == "restricted"
    ]
    actions: list[dict] = []
    for inc in incidents[:5]:
        for act in inc.actions:
            actions.append(
                {
                    "label": inc.customer_action or act.action_type,
                    "status": inc.customer_status,
                    "title": inc.title,
                }
            )
    last_gps = ch.latest_gps(auth["user_id"])
    if last_gps:
        location_status = "Location on"
    else:
        location_status = "No location yet"
    return HomeSummary(
        user_id=auth["user_id"],
        protection_status="On" if not settings.sentinel_maintenance_mode else "Paused",
        last_gps=last_gps,
        bank_status="Frozen (demo)" if status.get("restricted") else "Active",
        bank_restricted=bool(status.get("restricted")),
        verified_count=len(verified),
        needs_review_count=len(needs),
        frozen_count=len(frozen),
        reviewed_count=len(verified),
        suspicious_count=len(needs),
        urgent_incidents=len(frozen),
        recent_actions=actions[:10],
        location_status=location_status,
        integrations={
            "clickhouse": ch.mode,
            "mongodb": mongo.mode,
            "openai": get_openai_investigator().mode,
            "elevenlabs": get_elevenlabs_sos().mode,
        },
    )


@router.post("/v1/gps")
def ingest_gps(body: GpsIngestRequest, auth: dict = Depends(require_auth)) -> dict:
    ch = get_clickhouse_store()
    event = GpsEvent(
        user_id=auth["user_id"],
        device_id=auth["device_id"],
        event_timestamp=body.event_timestamp or datetime.now(timezone.utc),
        lat=body.lat,
        lon=body.lon,
        horizontal_accuracy_m=body.horizontal_accuracy_m,
        source=body.source,
        synthetic=body.synthetic,
    )
    saved = ch.insert_gps(event)
    return {
        "stored": True,
        "mode": ch.mode,
        "event": saved.model_dump(mode="json"),
        "note": "LIVE ClickHouse when mode=live; memory adapter otherwise",
    }


@router.get("/v1/gps")
def list_gps(limit: int = 100, auth: dict = Depends(require_auth)) -> dict:
    ch = get_clickhouse_store()
    rows = ch.query_gps(auth["user_id"], limit=min(limit, 500))
    return {
        "mode": ch.mode,
        "count": len(rows),
        "events": [r.model_dump(mode="json") for r in rows],
    }


@router.delete("/v1/gps")
def delete_gps(auth: dict = Depends(require_auth)) -> dict:
    ch = get_clickhouse_store()
    deleted = ch.delete_user_gps(auth["user_id"])
    return {"deleted": deleted, "mode": ch.mode, "user_id": auth["user_id"]}


@router.get("/v1/transactions")
def transactions(auth: dict = Depends(require_auth)) -> dict:
    ch = get_clickhouse_store()
    rows = ch.get_financial(auth["user_id"])
    return {
        "synthetic": True,
        "count": len(rows),
        "events": [r.model_dump(mode="json") for r in rows],
        "label": "Financial events",
    }


@router.post("/v1/events/financial")
def ingest_financial(body: FinancialIngestRequest, auth: dict = Depends(require_auth)) -> dict:
    ch = get_clickhouse_store()
    event = FinancialEvent(
        account_id=body.account_id,
        user_id=auth["user_id"],
        transaction_type=body.transaction_type,
        channel=body.channel,
        merchant=body.merchant,
        merchant_lat=body.merchant_lat,
        merchant_lon=body.merchant_lon,
        merchant_geo_confidence=body.merchant_geo_confidence,
        amount=body.amount,
        authorization_time=body.authorization_time,
        posting_time=body.posting_time or datetime.now(timezone.utc),
        metadata=body.metadata,
        synthetic=True,
    )
    saved = ch.insert_financial(event)
    incident = None
    if body.auto_investigate:
        incident = FraudInvestigatorService().investigate(
            user_id=auth["user_id"],
            title=f"Suspicious transaction: {body.merchant}",
            trigger_summary=f"suspicious transaction event_id={saved.event_id} {body.merchant}",
            trigger_event_ids=[saved.event_id],
            account_id=body.account_id,
            channel=body.channel.value,
        )
    return {
        "event": saved.model_dump(mode="json"),
        "incident": incident.model_dump(mode="json") if incident else None,
        "label": "Financial event",
    }


@router.post("/v1/events/security")
def ingest_security(event: SecurityEvent, auth: dict = Depends(require_auth)) -> dict:
    if event.user_id != auth["user_id"]:
        event.user_id = auth["user_id"]
    saved = get_clickhouse_store().insert_security(event)
    return {"event": saved.model_dump(mode="json"), "label": "Security event"}


@router.get("/v1/incidents")
def list_incidents(auth: dict = Depends(require_auth)) -> dict:
    incidents = get_mongo_store().list_incidents(auth["user_id"])
    return {"count": len(incidents), "incidents": [_public_incident(i) for i in incidents]}


@router.get("/v1/incidents/{incident_id}")
def get_incident(incident_id: str, auth: dict = Depends(require_auth)) -> dict:
    incident = get_mongo_store().get_incident(incident_id)
    if not incident or incident.user_id != auth["user_id"]:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _public_incident(incident)


@router.post("/v1/incidents/{incident_id}/actions/{action_id}")
def incident_action(incident_id: str, action_id: str, auth: dict = Depends(require_auth)) -> dict:
    """Consumer one-tap actions — no homework like calling a bank."""
    mongo = get_mongo_store()
    bank = MockBankService(mongo)
    bank.seed(auth["user_id"])
    incident = mongo.get_incident(incident_id)
    if not incident or incident.user_id != auth["user_id"]:
        raise HTTPException(status_code=404, detail="Alert not found")

    action_id = action_id.lower().strip()
    if action_id in {"confirm_ok", "dismiss", "looks_good"}:
        incident.customer_status = "Verified"
        incident.customer_summary = (
            "Thanks — you confirmed this activity looks fine. Sentinel will keep watching quietly."
        )
        incident.customer_action = "Confirmed by you"
        incident.status = "verified"
        incident.severity = "info"
        incident.available_actions = [{"id": "dismiss", "label": "Looks good"}]
        incident.updated_at = datetime.now(timezone.utc)
        mongo.save_incident(incident)
        return {"ok": True, "incident": _public_incident(incident)}

    if action_id in {"freeze", "freeze_account"}:
        result = bank.restrict(
            MockBankService.DEMO_ACCOUNT_ID,
            reason="Customer requested account freeze from Sentinel",
            incident_id=incident.incident_id,
            authorized=True,
        )
        incident.customer_status = "Account protected"
        incident.customer_summary = (
            "You froze your demo account. New transfers are blocked until you unfreeze."
        )
        incident.customer_action = "Account frozen by you"
        incident.status = "restricted"
        incident.severity = "critical"
        incident.available_actions = [
            {"id": "keep_frozen", "label": "Keep account frozen"},
            {"id": "unfreeze", "label": "Unfreeze my account"},
        ]
        incident.updated_at = datetime.now(timezone.utc)
        mongo.save_incident(incident)
        return {"ok": True, "bank": result, "incident": _public_incident(incident)}

    if action_id in {"unfreeze", "unrestrict"}:
        result = bank.unrestrict(MockBankService.DEMO_ACCOUNT_ID, authorized=True)
        incident.customer_status = "Verified"
        incident.customer_summary = (
            "Your demo account is active again. Sentinel will keep monitoring for new risks."
        )
        incident.customer_action = "Unfrozen by you"
        incident.status = "verified"
        incident.severity = "info"
        incident.available_actions = [{"id": "freeze", "label": "Freeze my account"}]
        incident.updated_at = datetime.now(timezone.utc)
        mongo.save_incident(incident)
        return {"ok": True, "bank": result, "incident": _public_incident(incident)}

    if action_id in {"keep_frozen"}:
        return {
            "ok": True,
            "message": "Account stays frozen.",
            "incident": _public_incident(incident),
        }

    raise HTTPException(status_code=400, detail=f"Unknown action {action_id}")


def _public_incident(incident) -> dict:
    """Strip engineer-only noise from API responses used by the consumer app."""
    data = incident.model_dump(mode="json")
    # Hide cryptic IDs from the primary consumer payload
    data.pop("evidence_ids", None)
    data.pop("tool_trace", None)
    data.pop("trigger_event_ids", None)
    data["reference"] = data.get("customer_when") or "Recent alert"
    return data


@router.get("/v1/bank/status")
def bank_status(auth: dict = Depends(require_auth)) -> dict:
    bank = MockBankService()
    bank.seed(auth["user_id"])
    return bank.get_status(MockBankService.DEMO_ACCOUNT_ID)


@router.post("/v1/bank/transfer")
def bank_transfer(req: MockTransferRequest, auth: dict = Depends(require_auth)) -> dict:
    if req.user_id != auth["user_id"]:
        req.user_id = auth["user_id"]
    bank = MockBankService()
    bank.seed(auth["user_id"])
    result = bank.transfer(req)
    return result.model_dump(mode="json")


@router.post("/v1/bank/recipients")
def add_recipient(recipient: str, auth: dict = Depends(require_auth)) -> dict:
    bank = MockBankService()
    bank.seed(auth["user_id"])
    acct = bank.add_recipient(MockBankService.DEMO_ACCOUNT_ID, recipient)
    return {"recipients": acct.recipients, "demo_label": "sentinel_bank"}


@router.post("/v1/bank/unrestrict")
def unrestrict(auth: dict = Depends(require_auth)) -> dict:
    bank = MockBankService()
    bank.seed(auth["user_id"])
    return bank.unrestrict(MockBankService.DEMO_ACCOUNT_ID, authorized=True)


@router.post("/v1/travel")
def add_travel(plan: TravelPlan, auth: dict = Depends(require_auth)) -> dict:
    plan.user_id = auth["user_id"]
    saved = get_mongo_store().save_travel(plan)
    return saved.model_dump(mode="json")


@router.get("/v1/travel")
def list_travel(auth: dict = Depends(require_auth)) -> dict:
    plans = get_mongo_store().list_travel(auth["user_id"])
    return {"plans": [p.model_dump(mode="json") for p in plans]}


@router.get("/v1/devices")
def list_devices(auth: dict = Depends(require_auth)) -> dict:
    devices = get_mongo_store().list_devices(auth["user_id"])
    return {"devices": [d.model_dump(mode="json") for d in devices]}


@router.post("/v1/demo/reset")
def reset_demo(auth: dict = Depends(require_auth)) -> dict:
    """Clear incidents/activity log and unfreeze demo bank. Preserves real GPS history."""
    mongo = get_mongo_store()
    ch = get_clickhouse_store()
    bank = MockBankService(mongo)
    bank.seed(auth["user_id"])
    cleared = mongo.clear_demo_data(auth["user_id"])
    synth = ch.clear_synthetic_finance_security(auth["user_id"])
    unrestrict = bank.unrestrict(MockBankService.DEMO_ACCOUNT_ID, authorized=True)
    return {
        "ok": True,
        "cleared_incidents": cleared.get("incidents", 0),
        "cleared_investigations": cleared.get("investigations", 0),
        "cleared_synthetic_events": synth,
        "bank_unrestricted": not bool(unrestrict.get("restricted", True)),
        "preserved": ["Real GPS history in ClickHouse", "Trusted devices", "AWS stacks"],
        "note": "Demo log reset. GPS observations were not deleted.",
    }


@router.post("/v1/demo/elevenlabs-sos")
def elevenlabs_sos(incident_id: str | None = None, auth: dict = Depends(require_auth)) -> dict:
    """Stretch D: live ElevenLabs TTS for AI fraud-hotline escalation."""
    result = get_elevenlabs_sos().escalate(
        incident_id=incident_id or "demo-sos",
        user_id=auth["user_id"],
        reason="Emergency fraud escalation",
    )
    get_clickhouse_store().record_telemetry(
        {
            "telemetry_id": f"el_{result.get('created_at', '')}",
            "incident_id": result.get("incident_id"),
            "user_id": auth["user_id"],
            "action": "elevenlabs_sos",
            "status": "ok" if result.get("success") else "failed",
            "evidence_refs": [],
            "payload": {
                k: v
                for k, v in result.items()
                if k not in {"script"}  # keep logs smaller; script available in API response
            },
        }
    )
    return result


@router.post("/v1/demo/scenarios/{name}")
def run_scenario(name: str, auth: dict = Depends(require_auth)) -> dict:
    runner = ScenarioRunner()
    mapping = {
        "restaurant_match": runner.run_restaurant_match,
        "restaurant_insufficient": runner.run_restaurant_insufficient,
        "colombia_online": runner.run_colombia_online,
        "colombia_card_present": runner.run_colombia_card_present,
        "account_takeover": runner.run_account_takeover,
    }
    fn = mapping.get(name)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Unknown scenario {name}")
    result = fn(auth["user_id"])
    # Serialize pydantic models; incidents use consumer-safe payload
    out: dict[str, Any] = {}
    for k, v in result.items():
        if k == "incident" and hasattr(v, "model_dump"):
            out[k] = _public_incident(v)
        elif hasattr(v, "model_dump"):
            out[k] = v.model_dump(mode="json")
        else:
            out[k] = v
    return out
