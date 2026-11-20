#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "ERROR: neither 'docker compose' nor 'docker-compose' found"
  exit 1
fi

echo "== 1. SQL reconcile check (if pg container is running) =="
if "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -q '^pg$'; then
  OUT=$("${COMPOSE[@]}" exec -T pg psql -U "${POSTGRES_USER:-cs}" -d "${POSTGRES_DB:-course_select}" -t -A -v ON_ERROR_STOP=1 -f /workspace/bench/reconcile.sql)
  if [ -n "$OUT" ]; then
    echo "ERROR: reconcile.sql found drift:"
    echo "$OUT"
    exit 1
  fi
  echo "reconcile ok"
else
  echo "pg container not running, skipping reconcile check"
fi

echo "== 2. Backend pytest (if backend/ exists) =="
if [ -f backend/pyproject.toml ] && "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -q '^api$'; then
  "${COMPOSE[@]}" exec -T api pytest tests/unit -x -q
  if git diff --name-only HEAD~1 2>/dev/null | grep -q 'services/enrollment'; then
    "${COMPOSE[@]}" exec -T api pytest tests/integration/test_concurrency.py -x -q
  fi
else
  echo "backend/api not ready yet, skipping pytest"
fi

echo "== 3. Frontend build (if frontend/ exists) =="
if [ -f frontend/package.json ]; then
  (cd frontend && npm run build --silent)
else
  echo "frontend not ready yet, skipping build"
fi

echo "== precheck ok =="
