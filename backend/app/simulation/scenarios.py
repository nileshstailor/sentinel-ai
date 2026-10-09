"""Demo Lab scenarios A/B/C — synthetic events through the real pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.agents.investigator import FraudInvestigatorService
from app.config import get_settings
from app.integrations.clickhouse_client import get_clickhouse_store
from app.integrations.mongodb_client import get_mongo_store
from app.models.schemas import Channel, FinancialEvent, GpsEvent, SecurityEvent, TrustedDevice
from app.simulation.mock_bank import MockBankService


# San Francisco / Miami / Bogota reference points
SF = (37.7749, -122.4194)
MIAMI = (25.7617, -80.1918)
SF_RESTAURANT = (37.7879, -122.4075)  # near Union Square
BOGOTA = (4.7110, -74.0721)


class ScenarioRunner:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.ch = get_clickhouse_store()
        self.mongo = get_mongo_store()
        self.bank = MockBankService(self.mongo)
        self.investigator = FraudInvestigatorService(
            ch=self.ch, mongo=self.mongo, bank=self.bank
        )

    def ensure_baseline(self, user_id: str) -> None:
        self.bank.seed(user_id)
        now = datetime.now(timezone.utc)
        devices = self.mongo.list_devices(user_id)
        if not devices:
            self.mongo.save_device(
                TrustedDevice(
                    device_id=self.settings.sentinel_demo_device_id,
                    user_id=user_id,
                    label="Primary iPhone",
                    is_primary=True,
                    is_backup=False,
                    registered_at=now - timedelta(days=120),
                )
            )
            self.mongo.save_device(
                TrustedDevice(
                    device_id="backup-ipad-001",
                    user_id=user_id,
                    label="Backup iPad",
                    is_primary=False,
                    is_backup=True,
                    registered_at=now - timedelta(days=90),
                )
            )

    def run_restaurant_match(self, user_id: str) -> dict:
        """Scenario A — delayed SF restaurant with GPS match."""
        self.ensure_baseline(user_id)
        now = datetime.now(timezone.utc)
        auth_time = now - timedelta(days=5)
        # Miami then SF trip GPS
        for i, (lat, lon) in enumerate(
            [
                (MIAMI[0], MIAMI[1]),
                (MIAMI[0] + 0.01, MIAMI[1]),
                (SF[0], SF[1]),
                (SF_RESTAURANT[0], SF_RESTAURANT[1]),
                (SF_RESTAURANT[0] + 0.0003, SF_RESTAURANT[1] - 0.0002),
            ]
        ):
            self.ch.insert_gps(
                GpsEvent(
                    user_id=user_id,
                    device_id=self.settings.sentinel_demo_device_id,
                    event_timestamp=auth_time - timedelta(days=2) + timedelta(hours=i * 6),
                    lat=lat,
                    lon=lon,
                    horizontal_accuracy_m=12.0,
                    source="demo_seed_real_pipeline",
                    synthetic=True,
                )
            )
        # Visit near restaurant at authorization time
        visit = self.ch.insert_gps(
            GpsEvent(
                user_id=user_id,
                device_id=self.settings.sentinel_demo_device_id,
                event_timestamp=auth_time,
                lat=SF_RESTAURANT[0],
                lon=SF_RESTAURANT[1],
                horizontal_accuracy_m=10.0,
                source="demo_seed_real_pipeline",
                synthetic=True,
            )
        )
        fin = self.ch.insert_financial(
            FinancialEvent(
                account_id=MockBankService.DEMO_ACCOUNT_ID,
                user_id=user_id,
                channel=Channel.CARD_PRESENT,
                merchant="Zuni Café",
                merchant_lat=SF_RESTAURANT[0],
                merchant_lon=SF_RESTAURANT[1],
                merchant_geo_confidence=0.9,
                amount=86.40,
                authorization_time=auth_time,
                posting_time=now,
                metadata={"scenario": "A_match", "delayed_posting": True},
            )
        )
        incident = self.investigator.investigate(
            user_id=user_id,
            title="Restaurant charge verified",
            trigger_summary=f"delayed restaurant posting event_id={fin.event_id}",
            trigger_event_ids=[fin.event_id, visit.event_id],
            scenario="A_restaurant_match",
            channel=Channel.CARD_PRESENT.value,
        )
        return {"scenario": "A_restaurant_match", "incident": incident, "financial_event_id": fin.event_id}

    def run_restaurant_insufficient(self, user_id: str) -> dict:
        """Scenario A — delayed restaurant without GPS match."""
        self.ensure_baseline(user_id)
        now = datetime.now(timezone.utc)
        auth_time = now - timedelta(days=8)
        # Only Miami GPS — no SF restaurant visit
        self.ch.insert_gps(
            GpsEvent(
                user_id=user_id,
                device_id=self.settings.sentinel_demo_device_id,
                event_timestamp=auth_time,
                lat=MIAMI[0],
                lon=MIAMI[1],
                horizontal_accuracy_m=20.0,
                source="demo_seed_real_pipeline",
                synthetic=True,
            )
        )
        fin = self.ch.insert_financial(
            FinancialEvent(
                account_id=MockBankService.DEMO_ACCOUNT_ID,
                user_id=user_id,
                channel=Channel.CARD_PRESENT,
                merchant="Cotogna",
                merchant_lat=SF_RESTAURANT[0],
                merchant_lon=SF_RESTAURANT[1],
                merchant_geo_confidence=0.7,
                amount=54.20,
                authorization_time=auth_time,
                posting_time=now,
                metadata={"scenario": "A_insufficient"},
            )
        )
        incident = self.investigator.investigate(
            user_id=user_id,
            title="Restaurant charge needs review",
            trigger_summary=f"delayed restaurant insufficient evidence event_id={fin.event_id}",
            trigger_event_ids=[fin.event_id],
            scenario="A_restaurant_insufficient",
            channel=Channel.CARD_PRESENT.value,
        )
        return {"scenario": "A_restaurant_insufficient", "incident": incident}

    def run_colombia_online(self, user_id: str) -> dict:
        """Scenario B — Colombia online merchant should NOT auto-freeze."""
        self.ensure_baseline(user_id)
        now = datetime.now(timezone.utc)
        self.ch.insert_gps(
            GpsEvent(
                user_id=user_id,
                device_id=self.settings.sentinel_demo_device_id,
                event_timestamp=now - timedelta(minutes=30),
                lat=SF[0],
                lon=SF[1],
                horizontal_accuracy_m=8.0,
                source="demo_seed_real_pipeline",
                synthetic=True,
            )
        )
        fin = self.ch.insert_financial(
            FinancialEvent(
                account_id=MockBankService.DEMO_ACCOUNT_ID,
                user_id=user_id,
                channel=Channel.CARD_NOT_PRESENT,
                merchant="Bogota Craft Market Online",
                merchant_lat=BOGOTA[0],
                merchant_lon=BOGOTA[1],
                merchant_geo_confidence=0.6,
                amount=129.00,
                authorization_time=now - timedelta(hours=1),
                posting_time=now,
                metadata={"scenario": "B_colombia_online"},
            )
        )
        incident = self.investigator.investigate(
            user_id=user_id,
            title="Colombia online merchant anomaly",
            trigger_summary=f"colombia online bogota merchant event_id={fin.event_id}",
            trigger_event_ids=[fin.event_id],
            scenario="B_colombia_online",
            channel=Channel.CARD_NOT_PRESENT.value,
        )
        status = self.bank.get_status(MockBankService.DEMO_ACCOUNT_ID)
        return {
            "scenario": "B_colombia_online",
            "incident": incident,
            "bank_restricted": status.get("restricted"),
            "expectation": "Should NOT auto-restrict on CNP alone",
        }

    def run_colombia_card_present(self, user_id: str) -> dict:
        """Scenario B variant — card-present Colombia with stronger signals."""
        self.ensure_baseline(user_id)
        now = datetime.now(timezone.utc)
        self.ch.insert_gps(
            GpsEvent(
                user_id=user_id,
                device_id=self.settings.sentinel_demo_device_id,
                event_timestamp=now - timedelta(minutes=10),
                lat=SF[0],
                lon=SF[1],
                horizontal_accuracy_m=8.0,
                source="demo_seed_real_pipeline",
                synthetic=True,
            )
        )
        for etype, detail in [
            ("new_device", {"device_id": "unknown-android-99"}),
            ("mfa_change", {"method": "sms_to_new_number"}),
            ("new_recipient", {"recipient": "bogota.cashout@example.com"}),
        ]:
            self.ch.insert_security(
                SecurityEvent(
                    user_id=user_id,
                    account_id=MockBankService.DEMO_ACCOUNT_ID,
                    event_type=etype,
                    timestamp=now - timedelta(minutes=40),
                    details=detail,
                )
            )
        fin = self.ch.insert_financial(
            FinancialEvent(
                account_id=MockBankService.DEMO_ACCOUNT_ID,
                user_id=user_id,
                channel=Channel.CARD_PRESENT,
                merchant="Bogota Electronics Plaza",
                merchant_lat=BOGOTA[0],
                merchant_lon=BOGOTA[1],
                merchant_geo_confidence=0.85,
                amount=890.00,
                authorization_time=now - timedelta(minutes=20),
                posting_time=now,
                metadata={"scenario": "B_colombia_card_present"},
            )
        )
        incident = self.investigator.investigate(
            user_id=user_id,
            title="Colombia card-present anomaly",
            trigger_summary=f"colombia card-present bogota event_id={fin.event_id}",
            trigger_event_ids=[fin.event_id],
            scenario="B_colombia_card_present",
            channel=Channel.CARD_PRESENT.value,
            security_signals=["new_device", "mfa_change", "new_recipient", "transfer_attempt"],
        )
        return {"scenario": "B_colombia_card_present", "incident": incident}

    def run_account_takeover(self, user_id: str) -> dict:
        """Scenario C — stolen phone / account takeover → restrict → reject transfer."""
        self.ensure_baseline(user_id)
        # Ensure unrestricted start
        acct = self.bank.seed(user_id)
        if acct.restricted:
            self.bank.unrestrict(acct.account_id, authorized=True)

        now = datetime.now(timezone.utc)
        for etype, detail in [
            ("failed_login", {"count": 4}),
            ("new_device", {"device_id": "attacker-phone-777"}),
            ("mfa_change", {"method": "email_recovery_reset"}),
            ("new_recipient", {"recipient": "attacker-cashout@evil.example"}),
        ]:
            self.ch.insert_security(
                SecurityEvent(
                    user_id=user_id,
                    account_id=MockBankService.DEMO_ACCOUNT_ID,
                    event_type=etype,
                    timestamp=now - timedelta(minutes=15),
                    device_id="attacker-phone-777",
                    details=detail,
                )
            )
        self.bank.add_recipient(MockBankService.DEMO_ACCOUNT_ID, "attacker-cashout@evil.example")
        fin = self.ch.insert_financial(
            FinancialEvent(
                account_id=MockBankService.DEMO_ACCOUNT_ID,
                user_id=user_id,
                transaction_type="transfer",
                channel=Channel.ZELLE_LIKE,
                merchant="Transfer to attacker-cashout@evil.example",
                amount=2000.00,
                authorization_time=now - timedelta(minutes=5),
                posting_time=now,
                metadata={"scenario": "C_takeover", "risky_transfer": True},
            )
        )
        incident = self.investigator.investigate(
            user_id=user_id,
            title="Stolen phone / account takeover",
            trigger_summary=(
                f"stolen phone account takeover mfa new_device recipient transfer "
                f"event_id={fin.event_id}"
            ),
            trigger_event_ids=[fin.event_id],
            scenario="C_account_takeover",
            channel=Channel.ZELLE_LIKE.value,
            security_signals=["new_device", "mfa_change", "new_recipient", "transfer"],
        )

        from app.models.schemas import MockTransferRequest

        transfer = self.bank.transfer(
            MockTransferRequest(
                account_id=MockBankService.DEMO_ACCOUNT_ID,
                user_id=user_id,
                amount=500.0,
                recipient="attacker-cashout@evil.example",
                memo="Post-restriction probe",
            )
        )
        status = self.bank.get_status(MockBankService.DEMO_ACCOUNT_ID)
        return {
            "scenario": "C_account_takeover",
            "incident": incident,
            "bank_status": status,
            "subsequent_transfer": transfer,
            "expectation": "Transfer must be rejected_restricted",
        }
