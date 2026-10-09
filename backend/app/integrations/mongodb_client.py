"""MongoDB Atlas client with in-memory fallback for offline unit tests."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.config import Settings, get_settings
from app.models.schemas import (
    Incident,
    InvestigationRecord,
    MockBankAccount,
    TravelPlan,
    TrustedDevice,
)

logger = logging.getLogger(__name__)


class MongoStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._db = None
        self.mode = "memory"
        self._lock = Lock()
        self._incidents: dict[str, Incident] = {}
        self._investigations: dict[str, InvestigationRecord] = {}
        self._accounts: dict[str, MockBankAccount] = {}
        self._devices: dict[str, TrustedDevice] = {}
        self._travel: dict[str, TravelPlan] = {}
        self._policies: dict[str, dict[str, Any]] = {}
        if self.settings.mongodb_enabled():
            self._connect()

    def _connect(self) -> None:
        try:
            from pymongo import MongoClient

            self._client = MongoClient(self.settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            self._client.admin.command("ping")
            self._db = self._client[self.settings.mongodb_database]
            self.mode = "live"
            logger.info("MongoDB LIVE connected")
        except Exception as exc:  # noqa: BLE001
            logger.warning("MongoDB live connect failed, using memory adapter: %s", exc)
            self._client = None
            self._db = None
            self.mode = "memory"

    def save_incident(self, incident: Incident) -> Incident:
        if self._db is not None:
            self._db.incidents.replace_one(
                {"incident_id": incident.incident_id},
                incident.model_dump(mode="json"),
                upsert=True,
            )
            return incident
        with self._lock:
            self._incidents[incident.incident_id] = incident
        return incident

    def list_incidents(self, user_id: str) -> list[Incident]:
        if self._db is not None:
            docs = list(self._db.incidents.find({"user_id": user_id}).sort("created_at", -1))
            return [i for i in (self._parse_incident(d) for d in docs) if i]
        with self._lock:
            rows = [i for i in self._incidents.values() if i.user_id == user_id]
            return sorted(rows, key=lambda i: i.created_at, reverse=True)

    def get_incident(self, incident_id: str) -> Incident | None:
        if self._db is not None:
            doc = self._db.incidents.find_one({"incident_id": incident_id})
            return self._parse_incident(doc)
        with self._lock:
            return self._incidents.get(incident_id)

    @staticmethod
    def _parse_incident(doc: dict[str, Any] | None) -> Incident | None:
        if not doc:
            return None
        clean = {k: v for k, v in doc.items() if k != "_id"}
        try:
            return Incident.model_validate(clean)
        except Exception:
            logger.warning("Skipping invalid incident %s", clean.get("incident_id"))
            return None

    def clear_demo_data(self, user_id: str) -> dict[str, int]:
        """Clear incidents/investigations for a clean demo log. Keeps trusted devices."""
        deleted = {"incidents": 0, "investigations": 0}
        if self._db is not None:
            deleted["incidents"] = self._db.incidents.delete_many({"user_id": user_id}).deleted_count
            deleted["investigations"] = self._db.investigations.delete_many(
                {"user_id": user_id}
            ).deleted_count
            return deleted
        with self._lock:
            before_i = len(self._incidents)
            self._incidents = {k: v for k, v in self._incidents.items() if v.user_id != user_id}
            deleted["incidents"] = before_i - len(self._incidents)
            before_v = len(self._investigations)
            self._investigations = {
                k: v for k, v in self._investigations.items() if v.user_id != user_id
            }
            deleted["investigations"] = before_v - len(self._investigations)
        return deleted

    def save_investigation(self, record: InvestigationRecord) -> InvestigationRecord:
        if self._db is not None:
            self._db.investigations.replace_one(
                {"investigation_id": record.investigation_id},
                record.model_dump(mode="json"),
                upsert=True,
            )
            return record
        with self._lock:
            self._investigations[record.investigation_id] = record
        return record

    def save_account(self, account: MockBankAccount) -> MockBankAccount:
        if self._db is not None:
            self._db.accounts.replace_one(
                {"account_id": account.account_id},
                account.model_dump(mode="json"),
                upsert=True,
            )
            return account
        with self._lock:
            self._accounts[account.account_id] = account
        return account

    def get_account(self, account_id: str) -> MockBankAccount | None:
        if self._db is not None:
            doc = self._db.accounts.find_one({"account_id": account_id})
            return self._parse_account(doc)
        with self._lock:
            return self._accounts.get(account_id)

    def list_accounts(self, user_id: str) -> list[MockBankAccount]:
        if self._db is not None:
            docs = list(self._db.accounts.find({"user_id": user_id}))
            return [a for a in (self._parse_account(d) for d in docs) if a]
        with self._lock:
            return [a for a in self._accounts.values() if a.user_id == user_id]

    @staticmethod
    def _parse_account(doc: dict[str, Any] | None) -> MockBankAccount | None:
        if not doc:
            return None
        clean = {k: v for k, v in doc.items() if k != "_id"}
        try:
            return MockBankAccount.model_validate(clean)
        except Exception:
            logger.warning("Skipping invalid account document account_id=%s", clean.get("account_id"))
            return None

    def save_device(self, device: TrustedDevice) -> TrustedDevice:
        if self._db is not None:
            self._db.trusted_devices.replace_one(
                {"device_id": device.device_id, "user_id": device.user_id},
                device.model_dump(mode="json"),
                upsert=True,
            )
            return device
        with self._lock:
            self._devices[f"{device.user_id}:{device.device_id}"] = device
        return device

    def list_devices(self, user_id: str) -> list[TrustedDevice]:
        if self._db is not None:
            docs = list(self._db.trusted_devices.find({"user_id": user_id}))
            return [TrustedDevice.model_validate(d) for d in docs]
        with self._lock:
            return [d for d in self._devices.values() if d.user_id == user_id]

    def save_travel(self, plan: TravelPlan) -> TravelPlan:
        if self._db is not None:
            self._db.travel_plans.replace_one(
                {"plan_id": plan.plan_id},
                plan.model_dump(mode="json"),
                upsert=True,
            )
            return plan
        with self._lock:
            self._travel[plan.plan_id] = plan
        return plan

    def list_travel(self, user_id: str) -> list[TravelPlan]:
        if self._db is not None:
            docs = list(self._db.travel_plans.find({"user_id": user_id}))
            return [TravelPlan.model_validate(d) for d in docs]
        with self._lock:
            return [t for t in self._travel.values() if t.user_id == user_id]

    def get_policy(self, user_id: str) -> dict[str, Any]:
        default = {
            "user_id": user_id,
            "allow_level3_restrict": True,
            "require_backup_device_for_stolen_phone": True,
            "auto_restrict_on_takeover": True,
            "colombia_online_alone_is_not_fraud": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if self._db is not None:
            doc = self._db.policies.find_one({"user_id": user_id})
            return doc or default
        with self._lock:
            return self._policies.get(user_id, default)

    def save_policy(self, user_id: str, policy: dict[str, Any]) -> dict[str, Any]:
        policy = {**policy, "user_id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()}
        if self._db is not None:
            self._db.policies.replace_one({"user_id": user_id}, policy, upsert=True)
            return policy
        with self._lock:
            self._policies[user_id] = policy
        return policy


_store: MongoStore | None = None


def get_mongo_store() -> MongoStore:
    global _store
    if _store is None:
        _store = MongoStore()
    return _store


def reset_mongo_store_for_tests() -> MongoStore:
    global _store
    _store = MongoStore(Settings(use_live_mongodb="false"))
    return _store
