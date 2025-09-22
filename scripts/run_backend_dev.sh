#!/usr/bin/env bash
set -Eeuo pipefail

# Move to repo root
cd "$(dirname "$0")/.."

echo "[run] working dir: $(pwd)"
if [[ -f .env ]]; then
  echo "[run] loading .env with export (set -a)"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
else
  echo "[run] .env not found; continuing without it"
fi

echo "[run] starting backend: python -m backend.server"
exec python -m backend.server

