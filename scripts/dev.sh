#!/usr/bin/env bash
# Run FastAPI backend + Vite dev server concurrently.
# Vite proxies /api/* to the backend at localhost:9103.
# Usage: ./scripts/dev.sh
set -e

trap 'kill $(jobs -p) 2>/dev/null' EXIT

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting FastAPI backend on :9103..."
vacuum-dashboard --port 9103 --no-browser &

echo "Starting Vite dev server..."
cd "$REPO_ROOT/frontend" && npm run dev &

wait
