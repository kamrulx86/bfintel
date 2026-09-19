#!/usr/bin/env bash
# Deploy BFIntel to a remote host (rsync + optional compose rebuild).
set -euo pipefail

HOST="${LAB_HOST:?Set LAB_HOST to the target server hostname or IP}"
USER="${LAB_USER:-deploy}"
SSH_PORT="${SSH_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-~/bfintel}"
RSYNC_SSH="ssh -p ${SSH_PORT} -o BatchMode=yes"

rsync -avz -e "$RSYNC_SSH" \
  --exclude node_modules --exclude .venv --exclude __pycache__ --exclude .git \
  --exclude frontend/dist --exclude .env --exclude lab-setup.credentials \
  --exclude 'backend/.pytest_cache' --exclude 'backend/.ruff_cache' \
  "$(dirname "$0")/.." "${USER}@${HOST}:${REMOTE_DIR}/"

if [[ "${DEPLOY_COMPOSE:-0}" == "1" ]]; then
  ssh -p "$SSH_PORT" -o BatchMode=yes "${USER}@${HOST}" \
    "cd ${REMOTE_DIR} && sudo docker compose up -d --build"
fi

echo "Synced to ${USER}@${HOST}:${REMOTE_DIR}"
echo "Rebuild remotely: DEPLOY_COMPOSE=1 LAB_HOST=${HOST} SSH_PORT=${SSH_PORT} USER=${USER} $0"
