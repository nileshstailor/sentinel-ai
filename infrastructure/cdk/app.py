#!/usr/bin/env python3
"""CDK app entrypoint for Sentinel AI hackathon stacks."""

import aws_cdk as cdk

from sentinel_cdk.api_stack import SentinelApiStack
from sentinel_cdk.suspension_stack import SentinelSuspensionStack

app = cdk.App()

env = cdk.Environment(account="284981582445", region="us-east-1")
tags = {
    "Project": "SentinelAI-Hackathon",
    "SuspensionAt": "2026-10-12T06:00:00Z",
}

api = SentinelApiStack(
    app,
    "SentinelAI-Api",
    env=env,
    description="Sentinel AI API (Lambda + API Gateway). Deploy only after spend approval.",
)

SentinelSuspensionStack(
    app,
    "SentinelAI-Suspension",
    env=env,
    api_stack_name=api.stack_name,
    function_name_prefix="sentinel-",
    suspend_at_utc="2026-10-12T06:00:00Z",
    description="Independently hosted reversible suspension controller. Preserves all data.",
)

for k, v in tags.items():
    cdk.Tags.of(app).add(k, v)

app.synth()
