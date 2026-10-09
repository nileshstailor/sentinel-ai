"""Independently hosted reversible suspension controller.

Schedule: 2026-10-12T06:00:00Z (Sunday Oct 11, 2026 11:00 PM America/Los_Angeles)
Preserves ALL resources and data. Disables invocations only.
"""

from __future__ import annotations

from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_scheduler as scheduler,
    aws_sqs as sqs,
)
from constructs import Construct

CONTROLLER_DIR = Path(__file__).resolve().parents[1] / "suspension_controller"


class SentinelSuspensionStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        api_stack_name: str,
        function_name_prefix: str = "sentinel-",
        suspend_at_utc: str = "2026-10-12T06:00:00Z",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dlq = sqs.Queue(
            self,
            "SuspensionDLQ",
            queue_name="sentinel-suspension-dlq",
            retention_period=Duration.days(14),
        )

        controller = lambda_.Function(
            self,
            "SuspensionController",
            function_name="sentinel-suspension-controller",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset(str(CONTROLLER_DIR)),
            timeout=Duration.seconds(120),
            memory_size=256,
            # Do NOT set reserved concurrency to 0 — controller must remain operable.
            environment={
                "PROJECT_TAG": "SentinelAI-Hackathon",
                "FUNCTION_NAME_PREFIX": function_name_prefix,
                "API_STACK_NAME": api_stack_name,
                "SUSPEND_AT_UTC": suspend_at_utc,
                "STATE_BUCKET_PARAM": "sentinel-suspension-state",
                # Exclude self from suspension targets
                "EXCLUDE_FUNCTIONS": "sentinel-suspension-controller",
            },
            log_retention=logs.RetentionDays.TWO_WEEKS,
            dead_letter_queue=dlq,
            description="Reversible suspend/resume controller — never deletes data",
        )

        controller.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:ListFunctions",
                    "lambda:GetFunction",
                    "lambda:GetFunctionConcurrency",
                    "lambda:PutFunctionConcurrency",
                    "lambda:DeleteFunctionConcurrency",
                    "lambda:ListEventSourceMappings",
                    "lambda:UpdateEventSourceMapping",
                    "lambda:UpdateFunctionConfiguration",
                    "events:ListRules",
                    "events:DisableRule",
                    "events:EnableRule",
                    "events:ListTargetsByRule",
                    "scheduler:GetSchedule",
                    "scheduler:UpdateSchedule",
                    "apigateway:GET",
                    "apigateway:PATCH",
                    "apigateway:PUT",
                    "states:ListStateMachines",
                    "states:DescribeStateMachine",
                    "states:UpdateStateMachine",
                    "ssm:GetParameter",
                    "ssm:PutParameter",
                    "tag:GetResources",
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStackResources",
                ],
                resources=["*"],
            )
        )

        schedule_role = iam.Role(
            self,
            "SchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
            inline_policies={
                "invoke": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=[controller.function_arn],
                        )
                    ]
                )
            },
        )

        schedule = scheduler.CfnSchedule(
            self,
            "SundaySuspendSchedule",
            name="sentinel-sunday-suspend",
            description="Suspend Sentinel workloads Sunday Oct 11 2026 11PM PT — no deletions",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            schedule_expression=f"at({suspend_at_utc.replace('Z', '')})",
            schedule_expression_timezone="UTC",
            state="ENABLED",
            target=scheduler.CfnSchedule.TargetProperty(
                arn=controller.function_arn,
                role_arn=schedule_role.role_arn,
                input='{"action":"suspend","source":"eventbridge-scheduler"}',
                retry_policy=scheduler.CfnSchedule.RetryPolicyProperty(
                    maximum_event_age_in_seconds=3600,
                    maximum_retry_attempts=3,
                ),
                dead_letter_config=scheduler.CfnSchedule.DeadLetterConfigProperty(
                    arn=dlq.queue_arn,
                ),
            ),
        )

        # Grant scheduler permission on Lambda
        controller.add_permission(
            "AllowScheduler",
            principal=iam.ServicePrincipal("scheduler.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:scheduler:{self.region}:{self.account}:schedule/default/sentinel-sunday-suspend",
        )

        cdk.CfnOutput(self, "ControllerFunctionName", value=controller.function_name)
        cdk.CfnOutput(self, "ScheduleName", value=schedule.name or "sentinel-sunday-suspend")
        cdk.CfnOutput(self, "SuspendAtUtc", value=suspend_at_utc)
        cdk.CfnOutput(self, "DlqUrl", value=dlq.queue_url)

        self.controller = controller
