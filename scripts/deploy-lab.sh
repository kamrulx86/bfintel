#!/usr/bin/env bash
# Deploy BFIntel to Wazuh lab host (default 192.168.122.186)
set -euo pipefail

HOST="${LAB_HOST:-192.168.122.186}"
USER="${LAB_USER:-kamrul}"
REMOTE_DIR="${REMOTE_DIR:-~/bfintel}"

rsync -avz --exclude node_modules --exclude .venv --exclude __pycache__ --exclude .git \
  "$(dirname "$0")/.." "${USER}@${HOST}:${REMOTE_DIR}/"

echo "Run on remote: cd bfintel/WEB-EDGE && cp .env.example .env && docker compose up -d --build"
