"""Pytest fixtures — force in-memory adapters for deterministic unit tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["USE_LIVE_CLICKHOUSE"] = "false"
os.environ["USE_LIVE_MONGODB"] = "false"
os.environ["USE_LIVE_OPENAI"] = "false"
os.environ["OPENAI_API_KEY"] = ""
os.environ["CLICKHOUSE_HOST"] = ""
os.environ["MONGODB_URI"] = ""
os.environ["SENTINEL_API_TOKEN"] = "test-token"
os.environ["SENTINEL_MAINTENANCE_MODE"] = "false"


@pytest.fixture(autouse=True)
def _reset_stores():
    from app.config import get_settings
    from app.integrations.clickhouse_client import reset_clickhouse_store_for_tests
    from app.integrations.mongodb_client import reset_mongo_store_for_tests
    from app.integrations.openai_client import reset_openai_for_tests

    get_settings.cache_clear()
    reset_clickhouse_store_for_tests()
    reset_mongo_store_for_tests()
    reset_openai_for_tests()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer test-token",
        "X-Sentinel-User": "demo-user-001",
        "X-Sentinel-Device": "demo-iphone-001",
    }
