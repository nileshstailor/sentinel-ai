#!/usr/bin/env bash
set -euo pipefail
# Extend the EventBridge Scheduler one-time suspend deadline and verify read-back.
# Usage: NEW_EXPIRY_UTC=2026-10-18T06:00:00Z ./scripts/aws-extend-expiry.sh
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true
REGION="${AWS_REGION:-us-east-1}"
FN="${SUSPENSION_FN:-sentinel-suspension-controller}"

if [[ -z "${NEW_EXPIRY_UTC:-}" ]]; then
  echo "Set NEW_EXPIRY_UTC=YYYY-MM-DDTHH:MM:SSZ" >&2
  exit 1
fi

PAYLOAD=$(python3 -c "import json; print(json.dumps({'action':'extend','new_expiry_utc':'${NEW_EXPIRY_UTC}'}))")
aws lambda invoke \
  --function-name "$FN" \
  --payload "$PAYLOAD" \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  /tmp/sentinel-extend.json
python3 -m json.tool < /tmp/sentinel-extend.json

echo
echo "Read-back schedule:"
aws scheduler get-schedule --name sentinel-sunday-suspend --region "$REGION" \
  --query '{Expression:ScheduleExpression,State:State}' --output json
