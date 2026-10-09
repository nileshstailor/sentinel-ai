"""Load sponsor secrets from AWS Secrets Manager when running on Lambda."""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


def hydrate_env_from_secrets() -> None:
    arn = os.environ.get("SENTINEL_SECRETS_ARN") or os.environ.get("SENTINEL_SECRETS_NAME")
    if not arn:
        return
    try:
        import boto3

        client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        resp = client.get_secret_value(SecretId=arn)
        raw = resp.get("SecretString") or "{}"
        data = json.loads(raw)
        for key, value in data.items():
            if value and key not in os.environ:
                os.environ[key] = str(value)
        logger.info("Hydrated %d secret keys into environment", len(data))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Secrets hydration skipped: %s", exc)
