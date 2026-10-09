#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/backend/dist/lambda_src"
REQ="$ROOT/backend/requirements-lambda.txt"
rm -rf "$OUT"
mkdir -p "$OUT"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "Packaging slim Lambda deps with Docker..."
  docker run --rm \
    --platform linux/amd64 \
    -v "$ROOT/backend:/var/task" \
    -w /var/task \
    public.ecr.aws/sam/build-python3.12:latest \
    /bin/bash -c "
      set -e
      rm -rf dist/lambda_src
      mkdir -p dist/lambda_src
      pip install -r requirements-lambda.txt -t dist/lambda_src --quiet
      cp -R app migrations dist/lambda_src/
      # Prune junk
      find dist/lambda_src -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
      find dist/lambda_src -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true
      find dist/lambda_src -type d -name 'test' -exec rm -rf {} + 2>/dev/null || true
      rm -rf dist/lambda_src/boto3 dist/lambda_src/botocore dist/lambda_src/s3transfer \
             dist/lambda_src/bin dist/lambda_src/*.dist-info/RECORD 2>/dev/null || true
      # Drop heavy unused bits
      rm -rf dist/lambda_src/uvloop dist/lambda_src/httptools dist/lambda_src/watchfiles \
             dist/lambda_src/websockets dist/lambda_src/yaml dist/lambda_src/pygments 2>/dev/null || true
    "
else
  echo "Docker unavailable"
  exit 1
fi

SIZE=$(du -sm "$OUT" | awk '{print $1}')
echo "Packaged at $OUT (${SIZE}MB)"
if [[ "$SIZE" -gt 200 ]]; then
  echo "WARNING: package still large (${SIZE}MB). Listing top dirs:"
  du -sh "$OUT"/* | sort -hr | head -20
fi
