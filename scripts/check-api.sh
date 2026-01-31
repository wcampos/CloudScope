#!/usr/bin/env sh
# Check API connectivity (direct and via frontend proxy).
# Run from project root. Use after: docker compose up -d

set -e

API_DIRECT="${API_DIRECT:-http://localhost:5001}"
FRONTEND_PROXY="${FRONTEND_PROXY:-http://localhost:3000}"

echo "=== CloudScope API connection check ==="
echo ""

echo "1. Direct API ($API_DIRECT/health)"
if curl -sf "$API_DIRECT/health" > /dev/null; then
  echo "   OK"
else
  echo "   FAILED - Is the API running? (docker compose up -d)"
  exit 1
fi

echo "2. Direct API ($API_DIRECT/api/profiles)"
if curl -sf "$API_DIRECT/api/profiles" > /dev/null; then
  echo "   OK"
else
  echo "   FAILED"
  exit 1
fi

echo "3. Via frontend proxy ($FRONTEND_PROXY/health)"
if curl -sf "$FRONTEND_PROXY/health" > /dev/null; then
  echo "   OK"
else
  echo "   FAILED - Open the app at $FRONTEND_PROXY (not 5173 when using Docker)"
  exit 1
fi

echo "4. Via frontend proxy ($FRONTEND_PROXY/api/profiles)"
if curl -sf "$FRONTEND_PROXY/api/profiles" > /dev/null; then
  echo "   OK"
else
  echo "   FAILED"
  exit 1
fi

echo ""
echo "All checks passed. Use the app at: $FRONTEND_PROXY"
echo "  (Docker: http://localhost:3000  |  Dev: http://localhost:5173 with API on 5001)"
