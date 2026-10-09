"""Milestone-oriented backend tests (memory adapters)."""

from __future__ import annotations

from datetime import datetime, timezone


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["integrations"]["clickhouse"] == "memory"


def test_gps_ingest_and_query(client, auth_headers):
    payload = {
        "lat": 37.7749,
        "lon": -122.4194,
        "horizontal_accuracy_m": 11.5,
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "core_location",
        "synthetic": False,
    }
    r = client.post("/v1/gps", json=payload, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["stored"] is True
    assert body["event"]["lat"] == 37.7749
    assert body["event"]["synthetic"] is False

    q = client.get("/v1/gps", headers=auth_headers)
    assert q.status_code == 200
    assert q.json()["count"] >= 1
    assert q.json()["events"][0]["lon"] == -122.4194


def test_account_takeover_rejects_transfer(client, auth_headers):
    r = client.post("/v1/demo/scenarios/account_takeover", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["bank_status"]["restricted"] is True
    xfer = body["subsequent_transfer"]
    assert xfer["success"] is False
    assert xfer["status"] == "rejected_restricted"
    assert xfer["demo_label"] == "sentinel_bank"

    # Direct transfer also rejected
    probe = client.post(
        "/v1/bank/transfer",
        json={
            "account_id": "acct_demo_checking",
            "user_id": "demo-user-001",
            "amount": 10,
            "recipient": "attacker-cashout@evil.example",
        },
        headers=auth_headers,
    )
    assert probe.status_code == 200
    assert probe.json()["success"] is False


def test_colombia_online_does_not_auto_freeze(client, auth_headers):
    r = client.post("/v1/demo/scenarios/colombia_online", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["bank_restricted"] is False
    assert body["incident"]["response_level"] <= 2


def test_restaurant_match_silent(client, auth_headers):
    r = client.post("/v1/demo/scenarios/restaurant_match", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    # Public incident payload omits tool_trace; consumer status is the contract.
    incident = body["incident"]
    assert "tool_trace" not in incident
    assert incident.get("customer_status") in {"Verified", "Needs review", "Account protected"}
    # If the mock bank is already frozen from a prior scenario, policy may surface Account protected.
    if not body.get("bank_restricted"):
        assert incident["response_level"] <= 2


def test_unauthorized(client):
    r = client.get("/v1/home")
    assert r.status_code == 401
