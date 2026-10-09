#!/usr/bin/env bash
set -euo pipefail
# Immediate reversible suspend. Preserves ALL data and stacks. No deletions.
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true
REGION="${AWS_REGION:-us-east-1}"
FN="${SUSPENSION_FN:-sentinel-suspension-controller}"

echo "Invoking suspend on $FN (no deletions)..."
aws lambda invoke \
  --function-name "$FN" \
  --payload '{"action":"suspend","source":"manual"}' \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  /tmp/sentinel-suspend.json
python3 -m json.tool < /tmp/sentinel-suspend.json
echo
echo "Verify with: scripts/aws-status.sh"
