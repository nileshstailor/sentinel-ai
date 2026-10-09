"""Sentinel AI FastAPI application — deployable to AWS Lambda via Mangum."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.routes import router
from app.config import get_settings

logging.basicConfig(level=logging.INFO)

from app.services.secrets import hydrate_env_from_secrets

hydrate_env_from_secrets()
get_settings.cache_clear()
settings = get_settings()

app = FastAPI(
    title="Sentinel AI",
    description="Your money has a bodyguard. AWS-hosted fraud protection MVP.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# AWS Lambda entrypoint
handler = Mangum(app, lifespan="off")


@app.on_event("startup")
def seed_demo() -> None:
    from app.simulation.mock_bank import MockBankService

    MockBankService().seed(settings.sentinel_demo_user_id)
