#!/usr/bin/env bash
set -euo pipefail
# Read-back suspension schedule + controller status. Never deletes anything.
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true
REGION="${AWS_REGION:-us-east-1}"
FN="${SUSPENSION_FN:-sentinel-suspension-controller}"

echo "=== EventBridge Scheduler: sentinel-sunday-suspend ==="
aws scheduler get-schedule --name sentinel-sunday-suspend --region "$REGION" \
  --query '{Name:Name,Expression:ScheduleExpression,Timezone:ScheduleExpressionTimezone,State:State}' \
  --output json 2>&1 || echo "Schedule not deployed yet"

echo
echo "=== Controller status invoke ==="
aws lambda invoke \
  --function-name "$FN" \
  --payload '{"action":"status"}' \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  /tmp/sentinel-status.json >/dev/null 2>&1 && cat /tmp/sentinel-status.json | python3 -m json.tool \
  || echo "Controller not deployed yet"

echo
echo "=== Tagged Sentinel resources ==="
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=SentinelAI-Hackathon \
  --region "$REGION" \
  --query 'ResourceTagMappingList[].ResourceARN' \
  --output text 2>&1 || true
