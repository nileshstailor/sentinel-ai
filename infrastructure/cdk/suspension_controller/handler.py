"""Reversible suspension controller.

Actions: suspend | resume | status | extend
Never deletes stacks, databases, secrets, logs, or GPS history.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3

PROJECT_TAG = os.environ.get("PROJECT_TAG", "SentinelAI-Hackathon")
PREFIX = os.environ.get("FUNCTION_NAME_PREFIX", "sentinel-")
EXCLUDE = set(
    f.strip()
    for f in os.environ.get("EXCLUDE_FUNCTIONS", "sentinel-suspension-controller").split(",")
    if f.strip()
)
STATE_PARAM = os.environ.get("STATE_BUCKET_PARAM", "sentinel-suspension-state")
SUSPEND_AT = os.environ.get("SUSPEND_AT_UTC", "2026-10-12T06:00:00Z")

lambda_client = boto3.client("lambda")
events = boto3.client("events")
scheduler = boto3.client("scheduler")
ssm = boto3.client("ssm")
apigateway = boto3.client("apigateway")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    action = (event or {}).get("action") or "status"
    if action == "suspend":
        return suspend()
    if action == "resume":
        return resume(event)
    if action == "extend":
        return extend(event)
    return status()


def _load_state() -> dict[str, Any]:
    try:
        resp = ssm.get_parameter(Name=STATE_PARAM)
        return json.loads(resp["Parameter"]["Value"])
    except ssm.exceptions.ParameterNotFound:
        return {}
    except Exception:
        return {}


def _save_state(state: dict[str, Any]) -> None:
    ssm.put_parameter(
        Name=STATE_PARAM,
        Value=json.dumps(state),
        Type="String",
        Overwrite=True,
    )


def _project_functions() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    paginator = lambda_client.get_paginator("list_functions")
    for page in paginator.paginate():
        for fn in page.get("Functions", []):
            name = fn["FunctionName"]
            if name in EXCLUDE:
                continue
            if name.startswith(PREFIX) or PROJECT_TAG.lower() in name.lower():
                out.append(fn)
    return out


def suspend() -> dict[str, Any]:
    state = _load_state()
    saved_concurrency: dict[str, Any] = state.get("concurrency", {})
    disabled_mappings: list[str] = state.get("disabled_mappings", [])
    disabled_rules: list[str] = state.get("disabled_rules", [])
    actions: list[str] = []

    for fn in _project_functions():
        name = fn["FunctionName"]
        # Capture prior reserved concurrency
        try:
            conc = lambda_client.get_function_concurrency(FunctionName=name)
            saved_concurrency[name] = conc.get("ReservedConcurrentExecutions")
        except Exception:
            saved_concurrency[name] = None
        # Set reserved concurrency to 0 (blocks invocations)
        try:
            lambda_client.put_function_concurrency(
                FunctionName=name, ReservedConcurrentExecutions=0
            )
            actions.append(f"lambda_concurrency_0:{name}")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"lambda_concurrency_failed:{name}:{exc}")

        # Flip maintenance env when present
        try:
            cfg = lambda_client.get_function_configuration(FunctionName=name)
            env = cfg.get("Environment", {}).get("Variables", {}) or {}
            if "SENTINEL_MAINTENANCE_MODE" in env or name == "sentinel-api":
                env = {**env, "SENTINEL_MAINTENANCE_MODE": "true"}
                lambda_client.update_function_configuration(
                    FunctionName=name, Environment={"Variables": env}
                )
                actions.append(f"maintenance_true:{name}")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"maintenance_failed:{name}:{exc}")

    # Disable event source mappings for project functions
    for fn in _project_functions():
        name = fn["FunctionName"]
        try:
            maps = lambda_client.list_event_source_mappings(FunctionName=name)
            for m in maps.get("EventSourceMappings", []):
                uuid = m["UUID"]
                if m.get("State") == "Enabled":
                    lambda_client.update_event_source_mapping(UUID=uuid, Enabled=False)
                    disabled_mappings.append(uuid)
                    actions.append(f"mapping_disabled:{uuid}")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"mapping_failed:{name}:{exc}")

    # Disable EventBridge rules tagged/named sentinel
    try:
        rules = events.list_rules()
        for rule in rules.get("Rules", []):
            rname = rule["Name"]
            if "sentinel" in rname.lower() and rule.get("State") == "ENABLED":
                events.disable_rule(Name=rname)
                disabled_rules.append(rname)
                actions.append(f"rule_disabled:{rname}")
    except Exception as exc:  # noqa: BLE001
        actions.append(f"rules_failed:{exc}")

    new_state = {
        "suspended": True,
        "suspended_at": datetime.now(timezone.utc).isoformat(),
        "suspend_deadline_utc": SUSPEND_AT,
        "concurrency": saved_concurrency,
        "disabled_mappings": disabled_mappings,
        "disabled_rules": disabled_rules,
        "actions": actions,
        "preserved": [
            "CloudFormation stacks",
            "Lambda code",
            "API Gateway definitions",
            "Secrets Manager secrets",
            "CloudWatch logs",
            "ClickHouse GPS history (external)",
            "MongoDB incidents (external)",
        ],
    }
    _save_state(new_state)

    # Read-back verification
    verified = []
    for name in saved_concurrency:
        try:
            conc = lambda_client.get_function_concurrency(FunctionName=name)
            verified.append(
                {
                    "function": name,
                    "reserved": conc.get("ReservedConcurrentExecutions"),
                    "ok": conc.get("ReservedConcurrentExecutions") == 0,
                }
            )
        except Exception as exc:  # noqa: BLE001
            verified.append({"function": name, "ok": False, "error": str(exc)})

    return {
        "action": "suspend",
        "success": all(v.get("ok") for v in verified) if verified else True,
        "verified": verified,
        "state": new_state,
        "note": "No resources deleted. Residual storage/secrets/logs/scheduler costs may continue.",
    }


def resume(event: dict[str, Any]) -> dict[str, Any]:
    """Restore previously captured concurrency/triggers. Requires approved new expiry if past deadline."""
    state = _load_state()
    if not state.get("suspended"):
        return {"action": "resume", "success": True, "message": "Already active"}

    new_expiry = event.get("new_expiry_utc")
    now = datetime.now(timezone.utc)
    deadline = datetime.fromisoformat(SUSPEND_AT.replace("Z", "+00:00"))
    if now > deadline and not new_expiry:
        return {
            "action": "resume",
            "success": False,
            "message": "Past suspension deadline — provide approved new_expiry_utc and spend allowance",
        }

    actions: list[str] = []
    for name, prior in (state.get("concurrency") or {}).items():
        try:
            if prior is None:
                lambda_client.delete_function_concurrency(FunctionName=name)
            else:
                lambda_client.put_function_concurrency(
                    FunctionName=name, ReservedConcurrentExecutions=int(prior)
                )
            actions.append(f"concurrency_restored:{name}:{prior}")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"concurrency_restore_failed:{name}:{exc}")

        try:
            cfg = lambda_client.get_function_configuration(FunctionName=name)
            env = cfg.get("Environment", {}).get("Variables", {}) or {}
            if "SENTINEL_MAINTENANCE_MODE" in env:
                env["SENTINEL_MAINTENANCE_MODE"] = "false"
                if new_expiry:
                    env["SENTINEL_SUSPEND_AT_UTC"] = new_expiry
                lambda_client.update_function_configuration(
                    FunctionName=name, Environment={"Variables": env}
                )
        except Exception as exc:  # noqa: BLE001
            actions.append(f"maintenance_clear_failed:{name}:{exc}")

    for uuid in state.get("disabled_mappings") or []:
        try:
            lambda_client.update_event_source_mapping(UUID=uuid, Enabled=True)
            actions.append(f"mapping_enabled:{uuid}")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"mapping_enable_failed:{uuid}:{exc}")

    for rname in state.get("disabled_rules") or []:
        try:
            events.enable_rule(Name=rname)
            actions.append(f"rule_enabled:{rname}")
        except Exception as exc:  # noqa: BLE001
            actions.append(f"rule_enable_failed:{rname}:{exc}")

    state["suspended"] = False
    state["resumed_at"] = datetime.now(timezone.utc).isoformat()
    state["resume_actions"] = actions
    if new_expiry:
        state["suspend_deadline_utc"] = new_expiry
    _save_state(state)
    return {"action": "resume", "success": True, "state": state}


def extend(event: dict[str, Any]) -> dict[str, Any]:
    new_expiry = event.get("new_expiry_utc")
    if not new_expiry:
        return {"action": "extend", "success": False, "message": "new_expiry_utc required"}
    # Update schedule
    try:
        existing = scheduler.get_schedule(Name="sentinel-sunday-suspend")
        scheduler.update_schedule(
            Name="sentinel-sunday-suspend",
            FlexibleTimeWindow=existing["FlexibleTimeWindow"],
            ScheduleExpression=f"at({new_expiry.replace('Z', '')})",
            ScheduleExpressionTimezone="UTC",
            Target=existing["Target"],
            State="ENABLED",
        )
        # Read back
        verify = scheduler.get_schedule(Name="sentinel-sunday-suspend")
        state = _load_state()
        state["suspend_deadline_utc"] = new_expiry
        state["schedule_expression"] = verify.get("ScheduleExpression")
        _save_state(state)
        return {
            "action": "extend",
            "success": True,
            "schedule_expression": verify.get("ScheduleExpression"),
            "new_expiry_utc": new_expiry,
        }
    except Exception as exc:  # noqa: BLE001
        return {"action": "extend", "success": False, "error": str(exc)}


def status() -> dict[str, Any]:
    state = _load_state()
    schedule_info: dict[str, Any] = {}
    try:
        sch = scheduler.get_schedule(Name="sentinel-sunday-suspend")
        schedule_info = {
            "name": sch.get("Name"),
            "expression": sch.get("ScheduleExpression"),
            "timezone": sch.get("ScheduleExpressionTimezone"),
            "state": sch.get("State"),
        }
    except Exception as exc:  # noqa: BLE001
        schedule_info = {"error": str(exc)}

    functions = []
    for fn in _project_functions():
        name = fn["FunctionName"]
        try:
            conc = lambda_client.get_function_concurrency(FunctionName=name)
            reserved = conc.get("ReservedConcurrentExecutions")
        except Exception:
            reserved = None
        functions.append({"name": name, "reserved_concurrency": reserved})

    return {
        "action": "status",
        "configured_suspend_at_utc": SUSPEND_AT,
        "schedule": schedule_info,
        "state": state,
        "functions": functions,
        "controller_excluded": list(EXCLUDE),
        "preserves_data": True,
        "deletes_resources": False,
    }
