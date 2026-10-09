"""Functional simulated bank with enforceable transfer restrictions."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.integrations.mongodb_client import MongoStore, get_mongo_store
from app.models.schemas import (
    MockBankAccount,
    MockTransferRequest,
    MockTransferResult,
)


class MockBankService:
    """SIMULATED bank — persistent demo state, never a real FI."""

    DEMO_ACCOUNT_ID = "acct_demo_checking"

    def __init__(self, store: MongoStore | None = None) -> None:
        self.store = store or get_mongo_store()

    def seed(self, user_id: str) -> MockBankAccount:
        existing = self.store.get_account(self.DEMO_ACCOUNT_ID)
        if existing and existing.user_id == user_id:
            return existing
        account = MockBankAccount(
            account_id=self.DEMO_ACCOUNT_ID,
            user_id=user_id,
            display_name="Sentinel Checking",
            balance=5420.55,
            recipients=["alice@example.com"],
            audit_log=[
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "action": "seed",
                    "detail": "Initial account",
                }
            ],
        )
        return self.store.save_account(account)

    def get_status(self, account_id: str) -> dict:
        account = self.store.get_account(account_id)
        if not account:
            return {"exists": False, "demo_label": "sentinel_bank"}
        return {
            "exists": True,
            "account_id": account.account_id,
            "user_id": account.user_id,
            "balance": account.balance,
            "restricted": account.restricted,
            "restriction_reason": account.restriction_reason,
            "restriction_incident_id": account.restriction_incident_id,
            "recipients": account.recipients,
            "demo_label": "sentinel_bank",
        }

    def add_recipient(self, account_id: str, recipient: str) -> MockBankAccount:
        account = self._require(account_id)
        if recipient not in account.recipients:
            account.recipients.append(recipient)
        account.audit_log.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": "add_recipient",
                "recipient": recipient,
            }
        )
        return self.store.save_account(account)

    def restrict(
        self,
        account_id: str,
        *,
        reason: str,
        incident_id: str,
        authorized: bool,
    ) -> dict:
        if not authorized:
            return {
                "success": False,
                "executed": False,
                "verified": False,
                "message": "Policy did not authorize restriction",
                "demo_label": "sentinel_bank",
            }
        account = self._require(account_id)
        account.restricted = True
        account.restriction_reason = reason
        account.restriction_incident_id = incident_id
        account.audit_log.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": "restrict",
                "reason": reason,
                "incident_id": incident_id,
            }
        )
        saved = self.store.save_account(account)
        verified = bool(saved.restricted)
        return {
            "success": verified,
            "executed": True,
            "verified": verified,
            "restricted": saved.restricted,
            "reason": saved.restriction_reason,
            "incident_id": saved.restriction_incident_id,
            "demo_label": "sentinel_bank",
        }

    def unrestrict(self, account_id: str, *, authorized: bool) -> dict:
        if not authorized:
            return {"success": False, "message": "Not authorized", "demo_label": "sentinel_bank"}
        account = self._require(account_id)
        account.restricted = False
        account.restriction_reason = None
        account.restriction_incident_id = None
        account.audit_log.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": "unrestrict",
            }
        )
        self.store.save_account(account)
        return {"success": True, "restricted": False, "demo_label": "sentinel_bank"}

    def transfer(self, req: MockTransferRequest) -> MockTransferResult:
        account = self.store.get_account(req.account_id)
        if not account:
            return MockTransferResult(
                success=False,
                status="rejected",
                message="Unknown account",
                restricted=False,
            )
        if account.user_id != req.user_id:
            return MockTransferResult(
                success=False,
                status="rejected",
                message="User/account mismatch",
                restricted=False,
            )
        if account.restricted:
            account.audit_log.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "action": "transfer_rejected",
                    "amount": req.amount,
                    "recipient": req.recipient,
                    "reason": account.restriction_reason,
                }
            )
            self.store.save_account(account)
            return MockTransferResult(
                success=False,
                status="rejected_restricted",
                message=(
                    f"Transfer blocked by Sentinel protective restriction. "
                    f"Reason: {account.restriction_reason}"
                ),
                balance_after=account.balance,
                restricted=True,
            )
        if req.amount <= 0 or req.amount > account.balance:
            return MockTransferResult(
                success=False,
                status="rejected",
                message="Insufficient funds or invalid amount",
                balance_after=account.balance,
                restricted=False,
            )
        if req.recipient not in account.recipients:
            return MockTransferResult(
                success=False,
                status="rejected",
                message="Recipient not on file — add recipient first",
                balance_after=account.balance,
                restricted=False,
            )
        account.balance = round(account.balance - req.amount, 2)
        transfer_id = f"xfer_{uuid4().hex[:10]}"
        account.audit_log.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": "transfer_success",
                "transfer_id": transfer_id,
                "amount": req.amount,
                "recipient": req.recipient,
            }
        )
        self.store.save_account(account)
        return MockTransferResult(
            success=True,
            transfer_id=transfer_id,
            status="completed",
            message="Transfer completed",
            balance_after=account.balance,
            restricted=False,
        )

    def _require(self, account_id: str) -> MockBankAccount:
        account = self.store.get_account(account_id)
        if not account:
            raise ValueError(f"Unknown account {account_id}")
        return account
