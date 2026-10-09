"""API Gateway + Lambda FastAPI stack for Sentinel AI."""

from __future__ import annotations

from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_budgets as budgets,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

BACKEND_ROOT = Path(__file__).resolve().parents[3] / "backend"


class SentinelApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Secrets placeholder — populate after user provides credentials. RETAIN on delete.
        secret = secretsmanager.Secret(
            self,
            "SentinelSecrets",
            secret_name="sentinel-ai/hackathon",
            description="OpenAI / ClickHouse / MongoDB / API token for Sentinel AI",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"SENTINEL_API_TOKEN":"change-me"}',
                generate_string_key="placeholder",
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Package via scripts/package_lambda.sh before deploy for full deps.
        # Synth uses source asset; packaging script produces backend/dist/lambda.zip.
        code_path = BACKEND_ROOT / "dist" / "lambda_src"
        if not code_path.exists():
            code_path = BACKEND_ROOT

        fn = lambda_.Function(
            self,
            "ApiFunction",
            function_name="sentinel-api",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.main.handler",
            code=lambda_.Code.from_asset(
                str(code_path),
                exclude=[
                    "tests",
                    "**/__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    "dist",
                    ".venv",
                ],
            ),
            timeout=Duration.seconds(60),
            memory_size=512,
            reserved_concurrent_executions=5,
            environment={
                "SENTINEL_MAINTENANCE_MODE": "false",
                "SENTINEL_SUSPEND_AT_UTC": "2026-10-12T06:00:00Z",
                "SENTINEL_STACK_NAME": "SentinelAI-Hackathon",
                "AWS_ACCOUNT_ID": "284981582445",
                "SENTINEL_SECRETS_ARN": secret.secret_arn,
                "USE_LIVE_CLICKHOUSE": "auto",
                "USE_LIVE_MONGODB": "auto",
                "USE_LIVE_OPENAI": "auto",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Sentinel AI FastAPI via Mangum",
        )
        secret.grant_read(fn)
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[secret.secret_arn],
            )
        )

        api = apigw.LambdaRestApi(
            self,
            "SentinelApi",
            rest_api_name="sentinel-ai-api",
            handler=fn,
            proxy=True,
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=20,
                throttling_burst_limit=40,
                metrics_enabled=True,
            ),
            cloud_watch_role=True,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )

        # Advisory budget only — NOT a hard financial cap. Authorized max ~$300.
        budgets.CfnBudget(
            self,
            "SentinelHackathonBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=300, unit="USD"),
                budget_name="SentinelAI-Hackathon-300",
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=pct,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address="nstailor87@gmail.com",
                            subscription_type="EMAIL",
                        )
                    ],
                )
                for pct in (50, 80, 100)
            ],
        )

        cdk.CfnOutput(self, "ApiUrl", value=api.url)
        cdk.CfnOutput(self, "ApiFunctionName", value=fn.function_name)
        cdk.CfnOutput(self, "SecretsArn", value=secret.secret_arn)

        self.api_function = fn
        self.api_url = api.url
