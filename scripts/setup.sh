#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3.12 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt
pip install -q -r infrastructure/cdk/requirements.txt
cp -n .env.example .env || true
chmod +x scripts/*.sh
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
(cd ios/SentinelAI && xcodegen generate)
echo "Setup complete. Fill .env with sponsor credentials. Approve AWS spend before cdk deploy."
