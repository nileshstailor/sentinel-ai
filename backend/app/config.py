"""Runtime configuration. Secrets come from env / Secrets Manager — never hardcode."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sentinel_api_token: str = Field(default="dev-sentinel-token-change-me")
    sentinel_demo_user_id: str = Field(default="demo-user-001")
    sentinel_demo_device_id: str = Field(default="demo-iphone-001")

    aws_region: str = Field(default="us-east-1")
    aws_account_id: str = Field(default="284981582445")
    sentinel_stack_name: str = Field(default="SentinelAI-Hackathon")
    sentinel_suspend_at_utc: str = Field(default="2026-10-12T06:00:00Z")
    sentinel_maintenance_mode: bool = Field(default=False)

    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")

    clickhouse_host: str = Field(default="")
    clickhouse_port: int = Field(default=8443)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="default")
    clickhouse_secure: bool = Field(default=True)

    mongodb_uri: str = Field(default="")
    mongodb_database: str = Field(default="sentinel")

    elevenlabs_api_key: str = Field(default="")
    elevenlabs_voice_id: str = Field(default="")
    elevenlabs_agent_phone: str = Field(default="")

    use_live_clickhouse: Literal["auto", "true", "false"] = Field(default="auto")
    use_live_mongodb: Literal["auto", "true", "false"] = Field(default="auto")
    use_live_openai: Literal["auto", "true", "false"] = Field(default="auto")

    gps_ttl_days: int = Field(default=30)
    restaurant_lookback_days: int = Field(default=14)

    def clickhouse_enabled(self) -> bool:
        if self.use_live_clickhouse == "false":
            return False
        if self.use_live_clickhouse == "true":
            return bool(self.clickhouse_host and self.clickhouse_password)
        return bool(self.clickhouse_host and self.clickhouse_password)

    def mongodb_enabled(self) -> bool:
        if self.use_live_mongodb == "false":
            return False
        if self.use_live_mongodb == "true":
            return bool(self.mongodb_uri)
        return bool(self.mongodb_uri)

    def openai_enabled(self) -> bool:
        if self.use_live_openai == "false":
            return False
        if self.use_live_openai == "true":
            return bool(self.openai_api_key)
        return bool(self.openai_api_key)

    def elevenlabs_enabled(self) -> bool:
        return bool(self.elevenlabs_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
