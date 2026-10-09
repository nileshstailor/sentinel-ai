#!/usr/bin/env python3
"""Run all three fraud scenarios in-process (adapters) and print proofs."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_LIVE_CLICKHOUSE", "false")
os.environ.setdefault("USE_LIVE_MONGODB", "false")
os.environ.setdefault("USE_LIVE_OPENAI", "false")
os.environ.setdefault("SENTINEL_API_TOKEN", "test-token")

from app.config import get_settings  # noqa: E402
from app.integrations.clickhouse_client import reset_clickhouse_store_for_tests  # noqa: E402
from app.integrations.mongodb_client import reset_mongo_store_for_tests  # noqa: E402
from app.integrations.openai_client import reset_openai_for_tests  # noqa: E402
from app.simulation.scenarios import ScenarioRunner  # noqa: E402


def main() -> None:
    get_settings.cache_clear()
    reset_clickhouse_store_for_tests()
    reset_mongo_store_for_tests()
    reset_openai_for_tests()
    user = get_settings().sentinel_demo_user_id
    runner = ScenarioRunner()

    results = {
        "A_match": runner.run_restaurant_match(user),
        "A_insufficient": runner.run_restaurant_insufficient(user),
        "B_online": runner.run_colombia_online(user),
        "C_takeover": runner.run_account_takeover(user),
    }

    summary = {
        "A_match_level": results["A_match"]["incident"].response_level,
        "A_insufficient_level": results["A_insufficient"]["incident"].response_level,
        "B_online_restricted": results["B_online"]["bank_restricted"],
        "C_restricted": results["C_takeover"]["bank_status"]["restricted"],
        "C_transfer_status": results["C_takeover"]["subsequent_transfer"].status,
        "integrations_note": "This in-process run uses memory/simulated adapters. AWS+sponsors required for LIVE demo.",
    }
    print(json.dumps(summary, indent=2, default=str))
    assert summary["C_restricted"] is True
    assert summary["C_transfer_status"] == "rejected_restricted"
    assert summary["B_online_restricted"] is False
    print("DEMO PROOFS OK")


if __name__ == "__main__":
    main()
