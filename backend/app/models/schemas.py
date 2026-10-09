"""Pydantic domain models for Sentinel AI."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Channel(str, Enum):
    CARD_PRESENT = "card_present"
    CARD_NOT_PRESENT = "card_not_present"
    ZELLE_LIKE = "zelle_like"
    VENMO_LIKE = "venmo_like"
    ACH = "ach"
    OTHER = "other"


class ResponseLevel(int, Enum):
    ALLOW = 0
    SILENT = 1
    REVIEW = 2
    RESTRICT = 3
    EMERGENCY = 4


class GpsEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: _id("gps"))
    user_id: str
    device_id: str
    event_timestamp: datetime
    lat: float
    lon: float
    horizontal_accuracy_m: float = 25.0
    source: str = "core_location"
    received_at: datetime | None = None
    synthetic: bool = False


class FinancialEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: _id("fin"))
    account_id: str
    user_id: str
    transaction_type: str = "purchase"
    channel: Channel
    merchant: str
    merchant_lat: float | None = None
    merchant_lon: float | None = None
    merchant_geo_confidence: float = 0.0
    amount: float
    currency: str = "USD"
    authorization_time: datetime | None = None
    posting_time: datetime
    synthetic: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class SecurityEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: _id("sec"))
    user_id: str
    account_id: str
    event_type: str
    timestamp: datetime
    device_id: str | None = None
    source_lat: float | None = None
    source_lon: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    synthetic: bool = True


class TravelPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: _id("travel"))
    user_id: str
    destination: str
    start_date: datetime
    end_date: datetime
    notes: str = ""


class TrustedDevice(BaseModel):
    device_id: str
    user_id: str
    label: str
    is_primary: bool = False
    is_backup: bool = False
    registered_at: datetime


class MockBankAccount(BaseModel):
    account_id: str
    user_id: str
    display_name: str
    balance: float
    currency: str = "USD"
    restricted: bool = False
    restriction_reason: str | None = None
    restriction_incident_id: str | None = None
    recipients: list[str] = Field(default_factory=list)
    audit_log: list[dict[str, Any]] = Field(default_factory=list)


class MockTransferRequest(BaseModel):
    account_id: str
    user_id: str
    amount: float
    recipient: str
    memo: str = ""
    channel: Channel = Channel.ZELLE_LIKE


class MockTransferResult(BaseModel):
    success: bool
    transfer_id: str | None = None
    status: str
    message: str
    balance_after: float | None = None
    restricted: bool = False
    demo_label: str = "sentinel_bank"


class ProtectionAction(BaseModel):
    action_id: str = Field(default_factory=lambda: _id("act"))
    incident_id: str
    action_type: str
    authorized: bool
    executed: bool
    verified: bool
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentConclusion(BaseModel):
    incident_id: str
    summary: str
    risk_score: float
    response_level: ResponseLevel
    competing_explanations: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    openai_live: bool = False


class InvestigationRecord(BaseModel):
    investigation_id: str = Field(default_factory=lambda: _id("inv"))
    incident_id: str
    user_id: str
    conclusion: AgentConclusion
    policy_decision: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class Incident(BaseModel):
    incident_id: str = Field(default_factory=lambda: _id("inc"))
    user_id: str
    title: str
    scenario: str | None = None
    status: str = "open"
    severity: str = "medium"
    # Consumer-facing labels (keep technical fields for Demo Lab / engineers)
    customer_status: str = "Open"
    customer_summary: str = ""
    customer_action: str = "None"
    customer_findings: list[str] = Field(default_factory=list)
    available_actions: list[dict[str, str]] = Field(default_factory=list)
    customer_when: str = ""
    trigger_event_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    conclusion_summary: str = ""
    response_level: int = 0
    actions: list[ProtectionAction] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    synthetic_trigger: bool = True


class HomeSummary(BaseModel):
    user_id: str
    protection_status: str
    last_gps: GpsEvent | None = None
    bank_status: str
    bank_restricted: bool
    verified_count: int = 0
    needs_review_count: int = 0
    frozen_count: int = 0
    # Legacy counters kept for older clients
    reviewed_count: int = 0
    suspicious_count: int = 0
    urgent_incidents: int = 0
    recent_actions: list[dict[str, Any]]
    demo_labels: list[str] = Field(
        default_factory=lambda: [
            "GPS observations from device when location is on",
        ]
    )
    integrations: dict[str, str] = Field(default_factory=dict)
    location_status: str = "Unknown"
