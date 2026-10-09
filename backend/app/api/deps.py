"""Auth and shared dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.config import get_settings


def require_auth(
    request: Request,
    authorization: str | None = Header(default=None),
    x_sentinel_user: str | None = Header(default=None),
    x_sentinel_device: str | None = Header(default=None),
) -> dict:
    settings = get_settings()
    if settings.sentinel_maintenance_mode:
        # Allow health + suspension status paths only
        if not request.url.path.endswith(("/health", "/v1/system/status")):
            raise HTTPException(status_code=503, detail="Sentinel is in maintenance/suspended mode")

    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if token != settings.sentinel_api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "user_id": x_sentinel_user or settings.sentinel_demo_user_id,
        "device_id": x_sentinel_device or settings.sentinel_demo_device_id,
    }
