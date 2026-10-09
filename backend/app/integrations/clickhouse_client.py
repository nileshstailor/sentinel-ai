"""ClickHouse Cloud client with in-memory fallback for offline unit tests."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.config import Settings, get_settings
from app.models.schemas import FinancialEvent, GpsEvent, SecurityEvent

logger = logging.getLogger(__name__)


def _utc(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class ClickHouseStore:
    """LIVE when credentials present; otherwise in-memory ADAPTER for tests."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self.mode = "memory"
        self._gps: list[GpsEvent] = []
        self._financial: list[FinancialEvent] = []
        self._security: list[SecurityEvent] = []
        self._telemetry: list[dict[str, Any]] = []
        self._lock = Lock()
        if self.settings.clickhouse_enabled():
            self._connect()

    def _connect(self) -> None:
        try:
            import clickhouse_connect

            self._client = clickhouse_connect.get_client(
                host=self.settings.clickhouse_host,
                port=self.settings.clickhouse_port,
                username=self.settings.clickhouse_user,
                password=self.settings.clickhouse_password,
                database=self.settings.clickhouse_database,
                secure=self.settings.clickhouse_secure,
            )
            self.mode = "live"
            self.ensure_schema()
            logger.info("ClickHouse LIVE connected to %s", self.settings.clickhouse_host)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ClickHouse live connect failed, using memory adapter: %s", exc)
            self._client = None
            self.mode = "memory"

    def ensure_schema(self) -> None:
        if not self._client:
            return
        from pathlib import Path

        sql_path = Path(__file__).resolve().parents[2] / "migrations" / "clickhouse_schema.sql"
        raw = sql_path.read_text(encoding="utf-8")
        # Strip full-line comments before splitting on semicolons
        # (comments may contain ';' and must not create bogus statements).
        uncommented_lines = [
            ln for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("--")
        ]
        uncommented = "\n".join(uncommented_lines)
        statements = [s.strip() for s in uncommented.split(";") if s.strip()]
        for clean in statements:
            self._client.command(clean)

    def insert_gps(self, event: GpsEvent) -> GpsEvent:
        event.received_at = _utc(event.received_at or datetime.now(timezone.utc))
        event.event_timestamp = _utc(event.event_timestamp)
        if self._client:
            self._client.insert(
                "gps_events",
                [
                    [
                        event.event_id,
                        event.user_id,
                        event.device_id,
                        event.event_timestamp,
                        event.lat,
                        event.lon,
                        event.horizontal_accuracy_m,
                        event.source,
                        event.received_at,
                        1 if event.synthetic else 0,
                    ]
                ],
                column_names=[
                    "event_id",
                    "user_id",
                    "device_id",
                    "event_timestamp",
                    "lat",
                    "lon",
                    "horizontal_accuracy_m",
                    "source",
                    "received_at",
                    "synthetic",
                ],
            )
            return event
        with self._lock:
            self._gps.append(event)
        return event

    def query_gps(
        self,
        user_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
    ) -> list[GpsEvent]:
        start = _utc(start) if start else None
        end = _utc(end) if end else None
        if self._client:
            clauses = ["user_id = {uid:String}"]
            params: dict[str, Any] = {"uid": user_id, "lim": limit}
            if start:
                clauses.append("event_timestamp >= {start:DateTime64(3)}")
                params["start"] = start
            if end:
                clauses.append("event_timestamp <= {end:DateTime64(3)}")
                params["end"] = end
            sql = (
                "SELECT event_id, user_id, device_id, event_timestamp, lat, lon, "
                "horizontal_accuracy_m, source, received_at, synthetic FROM gps_events WHERE "
                + " AND ".join(clauses)
                + " ORDER BY event_timestamp DESC LIMIT {lim:UInt32}"
            )
            result = self._client.query(sql, parameters=params)
            out: list[GpsEvent] = []
            for row in result.result_rows:
                out.append(
                    GpsEvent(
                        event_id=row[0],
                        user_id=row[1],
                        device_id=row[2],
                        event_timestamp=_utc(row[3]),
                        lat=row[4],
                        lon=row[5],
                        horizontal_accuracy_m=row[6],
                        source=row[7],
                        received_at=_utc(row[8]),
                        synthetic=bool(row[9]),
                    )
                )
            return out
        with self._lock:
            rows = [e for e in self._gps if e.user_id == user_id]
            if start:
                rows = [e for e in rows if e.event_timestamp >= start]
            if end:
                rows = [e for e in rows if e.event_timestamp <= end]
            rows.sort(key=lambda e: e.event_timestamp, reverse=True)
            return rows[:limit]

    def latest_gps(self, user_id: str) -> GpsEvent | None:
        rows = self.query_gps(user_id, limit=1)
        return rows[0] if rows else None

    def insert_financial(self, event: FinancialEvent) -> FinancialEvent:
        event.posting_time = _utc(event.posting_time)
        if event.authorization_time:
            event.authorization_time = _utc(event.authorization_time)
        if self._client:
            self._client.insert(
                "financial_events",
                [
                    [
                        event.event_id,
                        event.account_id,
                        event.user_id,
                        event.transaction_type,
                        event.channel.value if hasattr(event.channel, "value") else str(event.channel),
                        event.merchant,
                        event.merchant_lat,
                        event.merchant_lon,
                        event.merchant_geo_confidence,
                        event.amount,
                        event.currency,
                        event.authorization_time,
                        event.posting_time,
                        1 if event.synthetic else 0,
                        json.dumps(event.metadata),
                    ]
                ],
                column_names=[
                    "event_id",
                    "account_id",
                    "user_id",
                    "transaction_type",
                    "channel",
                    "merchant",
                    "merchant_lat",
                    "merchant_lon",
                    "merchant_geo_confidence",
                    "amount",
                    "currency",
                    "authorization_time",
                    "posting_time",
                    "synthetic",
                    "metadata",
                ],
            )
            return event
        with self._lock:
            self._financial.append(event)
        return event

    def get_financial(self, user_id: str, event_id: str | None = None) -> list[FinancialEvent]:
        if self._client:
            if event_id:
                sql = (
                    "SELECT event_id, account_id, user_id, transaction_type, channel, merchant, "
                    "merchant_lat, merchant_lon, merchant_geo_confidence, amount, currency, "
                    "authorization_time, posting_time, synthetic, metadata FROM financial_events "
                    "WHERE user_id = {uid:String} AND event_id = {eid:String}"
                )
                result = self._client.query(sql, parameters={"uid": user_id, "eid": event_id})
            else:
                sql = (
                    "SELECT event_id, account_id, user_id, transaction_type, channel, merchant, "
                    "merchant_lat, merchant_lon, merchant_geo_confidence, amount, currency, "
                    "authorization_time, posting_time, synthetic, metadata FROM financial_events "
                    "WHERE user_id = {uid:String} ORDER BY posting_time DESC LIMIT 100"
                )
                result = self._client.query(sql, parameters={"uid": user_id})
            out: list[FinancialEvent] = []
            for row in result.result_rows:
                meta = row[14]
                if isinstance(meta, str):
                    meta = json.loads(meta) if meta else {}
                out.append(
                    FinancialEvent(
                        event_id=row[0],
                        account_id=row[1],
                        user_id=row[2],
                        transaction_type=row[3],
                        channel=row[4],
                        merchant=row[5],
                        merchant_lat=row[6],
                        merchant_lon=row[7],
                        merchant_geo_confidence=row[8],
                        amount=row[9],
                        currency=row[10],
                        authorization_time=_utc(row[11]) if row[11] else None,
                        posting_time=_utc(row[12]),
                        synthetic=bool(row[13]),
                        metadata=meta or {},
                    )
                )
            return out
        with self._lock:
            rows = [e for e in self._financial if e.user_id == user_id]
            if event_id:
                rows = [e for e in rows if e.event_id == event_id]
            return sorted(rows, key=lambda e: e.posting_time, reverse=True)

    def insert_security(self, event: SecurityEvent) -> SecurityEvent:
        event.timestamp = _utc(event.timestamp)
        if self._client:
            self._client.insert(
                "security_events",
                [
                    [
                        event.event_id,
                        event.user_id,
                        event.account_id,
                        event.event_type,
                        event.timestamp,
                        event.device_id,
                        event.source_lat,
                        event.source_lon,
                        json.dumps(event.details),
                        1 if event.synthetic else 0,
                    ]
                ],
                column_names=[
                    "event_id",
                    "user_id",
                    "account_id",
                    "event_type",
                    "event_timestamp",
                    "device_id",
                    "source_lat",
                    "source_lon",
                    "details",
                    "synthetic",
                ],
            )
            return event
        with self._lock:
            self._security.append(event)
        return event

    def get_security(self, user_id: str, hours: int = 72) -> list[SecurityEvent]:
        cutoff = datetime.now(timezone.utc).timestamp() - hours * 3600
        if self._client:
            sql = (
                "SELECT event_id, user_id, account_id, event_type, event_timestamp, device_id, "
                "source_lat, source_lon, details, synthetic FROM security_events "
                "WHERE user_id = {uid:String} AND event_timestamp >= now64(3) - INTERVAL {h:UInt32} HOUR "
                "ORDER BY event_timestamp DESC"
            )
            result = self._client.query(sql, parameters={"uid": user_id, "h": hours})
            out: list[SecurityEvent] = []
            for row in result.result_rows:
                details = row[8]
                if isinstance(details, str):
                    details = json.loads(details) if details else {}
                out.append(
                    SecurityEvent(
                        event_id=row[0],
                        user_id=row[1],
                        account_id=row[2],
                        event_type=row[3],
                        timestamp=_utc(row[4]),
                        device_id=row[5],
                        source_lat=row[6],
                        source_lon=row[7],
                        details=details or {},
                        synthetic=bool(row[9]),
                    )
                )
            return out
        with self._lock:
            return [
                e
                for e in self._security
                if e.user_id == user_id and e.timestamp.timestamp() >= cutoff
            ]

    def match_merchant_visits(
        self,
        user_id: str,
        merchant_lat: float,
        merchant_lon: float,
        around: datetime,
        radius_km: float = 0.5,
        lookback_days: int = 14,
        accuracy_budget_m: float = 150.0,
    ) -> dict[str, Any]:
        """Geospatial/temporal match. Absence of GPS is NOT proof of non-visit."""
        from datetime import timedelta

        around = _utc(around)
        start = around - timedelta(days=lookback_days)
        end = around + timedelta(hours=12)
        points = self.query_gps(user_id, start=start, end=end, limit=500)
        matches: list[dict[str, Any]] = []
        for p in points:
            dist_km = great_circle_km(p.lat, p.lon, merchant_lat, merchant_lon)
            effective_radius = radius_km + (max(p.horizontal_accuracy_m, 0) / 1000.0)
            if dist_km <= effective_radius and p.horizontal_accuracy_m <= accuracy_budget_m:
                matches.append(
                    {
                        "gps_event_id": p.event_id,
                        "distance_km": round(dist_km, 4),
                        "accuracy_m": p.horizontal_accuracy_m,
                        "event_timestamp": p.event_timestamp.isoformat(),
                        "synthetic_gps": p.synthetic,
                    }
                )
        return {
            "match_count": len(matches),
            "matches": matches[:10],
            "gps_points_considered": len(points),
            "caveat": "Absence of GPS does not prove the user never visited the merchant.",
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
        }

    def record_telemetry(self, payload: dict[str, Any]) -> None:
        payload = {**payload, "created_at": datetime.now(timezone.utc).isoformat()}
        if self._client:
            self._client.insert(
                "agent_telemetry",
                [
                    [
                        payload.get("telemetry_id", f"tel_{len(self._telemetry)}"),
                        payload.get("incident_id", ""),
                        payload.get("user_id", ""),
                        payload.get("action", ""),
                        payload.get("status", ""),
                        json.dumps(payload.get("evidence_refs", [])),
                        json.dumps(payload),
                        datetime.now(timezone.utc),
                    ]
                ],
                column_names=[
                    "telemetry_id",
                    "incident_id",
                    "user_id",
                    "action",
                    "status",
                    "evidence_refs",
                    "payload",
                    "created_at",
                ],
            )
            return
        with self._lock:
            self._telemetry.append(payload)

    def clear_synthetic_finance_security(self, user_id: str) -> dict[str, int]:
        """Remove synthetic finance/security rows for a clean demo. Preserves real GPS."""
        if self._client:
            self._client.command(
                "ALTER TABLE financial_events DELETE WHERE user_id = {uid:String} AND synthetic = 1",
                parameters={"uid": user_id},
            )
            self._client.command(
                "ALTER TABLE security_events DELETE WHERE user_id = {uid:String} AND synthetic = 1",
                parameters={"uid": user_id},
            )
            return {"financial": -1, "security": -1}  # async mutations
        with self._lock:
            before_f, before_s = len(self._financial), len(self._security)
            self._financial = [
                e for e in self._financial if not (e.user_id == user_id and e.synthetic)
            ]
            self._security = [
                e for e in self._security if not (e.user_id == user_id and e.synthetic)
            ]
            return {
                "financial": before_f - len(self._financial),
                "security": before_s - len(self._security),
            }

    def delete_user_gps(self, user_id: str) -> int:
        if self._client:
            self._client.command(
                "ALTER TABLE gps_events DELETE WHERE user_id = {uid:String}",
                parameters={"uid": user_id},
            )
            return -1  # async mutation
        with self._lock:
            before = len(self._gps)
            self._gps = [e for e in self._gps if e.user_id != user_id]
            return before - len(self._gps)


_store: ClickHouseStore | None = None


def get_clickhouse_store() -> ClickHouseStore:
    global _store
    if _store is None:
        _store = ClickHouseStore()
    return _store


def reset_clickhouse_store_for_tests() -> ClickHouseStore:
    global _store
    _store = ClickHouseStore(Settings(use_live_clickhouse="false"))
    return _store
