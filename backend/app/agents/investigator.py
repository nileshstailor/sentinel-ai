"""Autonomous investigation orchestration with typed tools."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.tools import ToolContext, execute_tool
from app.config import get_settings
from app.integrations.clickhouse_client import ClickHouseStore, get_clickhouse_store
from app.integrations.mongodb_client import MongoStore, get_mongo_store
from app.integrations.openai_client import OpenAIInvestigator, get_openai_investigator
from app.models.schemas import (
    AgentConclusion,
    Incident,
    InvestigationRecord,
    ProtectionAction,
    ResponseLevel,
)
from app.policies.security_policy import SecurityPolicyEngine
from app.services.customer_labels import alert_subtitle, build_customer_copy, friendly_title
from app.simulation.mock_bank import MockBankService


class FraudInvestigatorService:
    def __init__(
        self,
        ch: ClickHouseStore | None = None,
        mongo: MongoStore | None = None,
        openai: OpenAIInvestigator | None = None,
        bank: MockBankService | None = None,
        policy: SecurityPolicyEngine | None = None,
    ) -> None:
        self.ch = ch or get_clickhouse_store()
        self.mongo = mongo or get_mongo_store()
        self.openai = openai or get_openai_investigator()
        self.bank = bank or MockBankService(self.mongo)
        self.policy = policy or SecurityPolicyEngine()
        self.settings = get_settings()

    def investigate(
        self,
        *,
        user_id: str,
        title: str,
        trigger_summary: str,
        trigger_event_ids: list[str],
        scenario: str | None = None,
        account_id: str | None = None,
        channel: str | None = None,
        security_signals: list[str] | None = None,
    ) -> Incident:
        now = datetime.now(timezone.utc)
        incident = Incident(
            user_id=user_id,
            title=friendly_title(scenario, title),
            scenario=scenario,
            status="investigating",
            severity="medium",
            customer_status="Checking…",
            customer_summary="Sentinel is reviewing this activity.",
            customer_action="None",
            trigger_event_ids=trigger_event_ids,
            created_at=now,
            updated_at=now,
            synthetic_trigger=True,
        )
        self.mongo.save_incident(incident)

        pending_protection: dict[str, Any] = {}
        ctx = ToolContext(
            user_id=user_id,
            incident_id=incident.incident_id,
            account_id=account_id or MockBankService.DEMO_ACCOUNT_ID,
            ch=self.ch,
            mongo=self.mongo,
            bank=self.bank,
            pending_protection=pending_protection,
        )

        def tool_executor(name: str, args: dict[str, Any]) -> Any:
            return execute_tool(name, args, ctx)

        result = self.openai.run(
            user_id=user_id,
            incident_id=incident.incident_id,
            trigger_summary=trigger_summary,
            tool_executor=tool_executor,
        )
        raw = result["conclusion"]
        tool_trace = list(result.get("tool_trace") or [])
        # Guarantee merchant↔GPS match evidence for restaurant demos (even if the LLM skips the tool).
        if (scenario or "").lower().startswith("a_restaurant"):
            tool_trace = self._ensure_restaurant_match_trace(
                tool_trace, tool_executor, trigger_event_ids
            )
        conclusion = AgentConclusion(
            incident_id=incident.incident_id,
            summary=raw.get("summary", ""),
            risk_score=float(raw.get("risk_score", 0)),
            response_level=ResponseLevel(int(raw.get("response_level", 1))),
            competing_explanations=list(raw.get("competing_explanations") or []),
            missing_data=list(raw.get("missing_data") or []),
            evidence_ids=list(raw.get("evidence_ids") or []),
            tool_trace=tool_trace,
            recommended_actions=list(raw.get("recommended_actions") or []),
            openai_live=bool(result.get("openai_live")),
        )

        signals = security_signals or []
        for item in conclusion.tool_trace:
            if item.get("tool") == "get_security_events":
                events = item.get("result", {}).get("events") or item.get("result") or []
                if isinstance(events, list):
                    for e in events:
                        if isinstance(e, dict):
                            signals.append(str(e.get("event_type", "")))

        user_policy = self.mongo.get_policy(user_id)
        decision = self.policy.decide(
            conclusion,
            user_policy=user_policy,
            security_signals=signals,
            channel=channel,
        )

        actions: list[ProtectionAction] = []
        restricted = False
        if decision.get("approved") and decision.get("action") == "restrict_account":
            bank_result = self.bank.restrict(
                account_id or MockBankService.DEMO_ACCOUNT_ID,
                reason=conclusion.summary[:240],
                incident_id=incident.incident_id,
                authorized=True,
            )
            action = ProtectionAction(
                incident_id=incident.incident_id,
                action_type="restrict_account",
                authorized=True,
                executed=bool(bank_result.get("executed")),
                verified=bool(bank_result.get("verified")),
                details=bank_result,
                created_at=datetime.now(timezone.utc),
            )
            actions.append(action)
            restricted = bool(bank_result.get("verified"))
        elif decision.get("action") == "request_user_verification":
            actions.append(
                ProtectionAction(
                    incident_id=incident.incident_id,
                    action_type="request_user_verification",
                    authorized=True,
                    executed=True,
                    verified=True,
                    details={"reason": decision.get("reason")},
                    created_at=datetime.now(timezone.utc),
                )
            )

        level = int(decision.get("response_level", conclusion.response_level))
        # Restaurant paths: never freeze from leftover bank state; classify from GPS match evidence.
        effective_restricted = restricted
        effective_action = decision.get("action")
        if (scenario or "").lower().startswith("a_restaurant") and not restricted:
            effective_restricted = False
            from app.services.customer_labels import _gps_nearby_from_trace

            nearby = _gps_nearby_from_trace(list(conclusion.tool_trace or []))
            if nearby is True or (nearby is None and "match" in (scenario or "").lower()):
                effective_action = "silent_log"
                level = 1
            else:
                effective_action = "request_user_verification"
                level = 2

        labels = build_customer_copy(
            scenario=scenario,
            response_level=level,
            decision_action=effective_action,
            restricted=effective_restricted,
            tool_trace=list(conclusion.tool_trace or []),
        )

        incident.evidence_ids = conclusion.evidence_ids
        incident.tool_trace = conclusion.tool_trace
        incident.conclusion_summary = labels["customer_summary"]
        incident.response_level = level
        incident.actions = actions
        incident.customer_status = labels["customer_status"]
        incident.customer_summary = labels["customer_summary"]
        incident.customer_action = (
            labels["available_actions"][0]["label"] if labels.get("available_actions") else "None"
        )
        incident.customer_findings = list(labels.get("customer_findings") or [])
        incident.available_actions = list(labels.get("available_actions") or [])
        incident.customer_when = alert_subtitle(incident.created_at)
        incident.severity = labels["severity"]
        incident.status = labels["status"]
        incident.title = labels.get("title") or friendly_title(scenario, incident.title)
        incident.updated_at = datetime.now(timezone.utc)
        self.mongo.save_incident(incident)

        record = InvestigationRecord(
            incident_id=incident.incident_id,
            user_id=user_id,
            conclusion=conclusion,
            policy_decision=decision,
            created_at=datetime.now(timezone.utc),
        )
        self.mongo.save_investigation(record)
        self.ch.record_telemetry(
            {
                "telemetry_id": record.investigation_id,
                "incident_id": incident.incident_id,
                "user_id": user_id,
                "action": "investigation_complete",
                "status": incident.status,
                "evidence_refs": conclusion.evidence_ids,
                "policy": decision,
                "openai_live": conclusion.openai_live,
            }
        )
        return incident

    def _ensure_restaurant_match_trace(
        self,
        tool_trace: list,
        tool_executor,
        trigger_event_ids: list[str],
    ) -> list:
        if any(t.get("tool") == "match_merchant_to_visits" for t in tool_trace):
            return tool_trace
        event_id = trigger_event_ids[0] if trigger_event_ids else None
        txn = tool_executor("get_transaction_details", {"event_id": event_id}) if event_id else {}
        if not isinstance(txn, dict):
            return tool_trace
        mlat, mlon = txn.get("merchant_lat"), txn.get("merchant_lon")
        around = txn.get("authorization_time") or txn.get("posting_time")
        if mlat is None or mlon is None or not around:
            return tool_trace
        match = tool_executor(
            "match_merchant_to_visits",
            {
                "merchant_lat": mlat,
                "merchant_lon": mlon,
                "around_iso": str(around),
                "lookback_days": 14,
            },
        )
        tool_trace = list(tool_trace)
        if not any(t.get("tool") == "get_transaction_details" for t in tool_trace):
            tool_trace.append(
                {"tool": "get_transaction_details", "args": {"event_id": event_id}, "result": txn}
            )
        tool_trace.append(
            {
                "tool": "match_merchant_to_visits",
                "args": {"merchant_lat": mlat, "merchant_lon": mlon, "around_iso": str(around)},
                "result": match,
            }
        )
        return tool_trace
