#!/usr/bin/env bash
set -euo pipefail
# Resume previously suspended workloads using saved state. Never deletes data.
# If past deadline, pass NEW_EXPIRY_UTC=2026-10-15T06:00:00Z
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true
REGION="${AWS_REGION:-us-east-1}"
FN="${SUSPENSION_FN:-sentinel-suspension-controller}"

PAYLOAD='{"action":"resume","source":"manual"}'
if [[ -n "${NEW_EXPIRY_UTC:-}" ]]; then
  PAYLOAD=$(python3 -c "import json; print(json.dumps({'action':'resume','source':'manual','new_expiry_utc':'${NEW_EXPIRY_UTC}'}))")
fi

echo "Invoking resume on $FN..."
aws lambda invoke \
  --function-name "$FN" \
  --payload "$PAYLOAD" \
  --cli-binary-format raw-in-base64-out \
  --region "$REGION" \
  /tmp/sentinel-resume.json
python3 -m json.tool < /tmp/sentinel-resume.json
