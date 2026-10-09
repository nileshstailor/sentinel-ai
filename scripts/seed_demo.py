#!/usr/bin/env python3
"""Seed baseline demo account/devices via in-process adapters (unit/demo prep)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_LIVE_CLICKHOUSE", "false")
os.environ.setdefault("USE_LIVE_MONGODB", "false")
os.environ.setdefault("USE_LIVE_OPENAI", "false")

from app.config import get_settings  # noqa: E402
from app.simulation.mock_bank import MockBankService  # noqa: E402
from app.simulation.scenarios import ScenarioRunner  # noqa: E402


def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    bank = MockBankService()
    acct = bank.seed(settings.sentinel_demo_user_id)
    print("Seeded account:", acct.account_id, "balance=", acct.balance)
    runner = ScenarioRunner()
    runner.ensure_baseline(settings.sentinel_demo_user_id)
    print("Baseline devices/travel ready for", settings.sentinel_demo_user_id)


if __name__ == "__main__":
    main()
