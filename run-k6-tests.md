#!/usr/bin/env bash
# run-tests.sh
# Convenience script to run k6 tests against the local Docker setup.
# Prometheus remote-write is enabled — results appear in Grafana live.
#
# Usage:
#   chmod +x run-tests.sh
#   ./run-tests.sh spike
#   ./run-tests.sh soak
#   ./run-tests.sh load
#   ./run-tests.sh all
#
# Prerequisites:
#   - Docker Compose stack is up: docker compose up -d
#   - k6 is installed: https://k6.io/docs/get-started/installation/
#   - For the load test: set TEST_EMAIL and TEST_PASSWORD below

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL="http://localhost"                              # nginx on port 80
PROM_URL="http://localhost:9090/api/v1/write"           # Prometheus remote-write
TEST_EMAIL="${TEST_EMAIL:-your-test-user@example.com}"  # override with env var
TEST_PASSWORD="${TEST_PASSWORD:-yourpassword}"           # override with env var

K6_FLAGS="--out experimental-prometheus-rw"

export K6_PROMETHEUS_RW_SERVER_URL="${PROM_URL}"

# ── Helpers ───────────────────────────────────────────────────────────────────
run_spike() {
  echo ""
  echo "▶ Running SPIKE test (health endpoints) — ~1.5 min"
  echo "   Watch: http://localhost:3000"
  echo ""
  k6 run ${K6_FLAGS} \
    -e BASE_URL="${BASE_URL}" \
    test-spike-health.js
}

run_soak() {
  echo ""
  echo "▶ Running SOAK test (/ready/ DB endurance) — ~13 min"
  echo "   Watch: http://localhost:3000"
  echo ""
  k6 run ${K6_FLAGS} \
    -e BASE_URL="${BASE_URL}" \
    test-soak-ready.js
}

run_load() {
  echo ""
  echo "▶ Running LOAD test (login → security → notifications) — ~14 min"
  echo "   Watch: http://localhost:3000"
  echo "   Account: ${TEST_EMAIL}"
  echo ""
  k6 run ${K6_FLAGS} \
    -e BASE_URL="${BASE_URL}" \
    -e TEST_EMAIL="${TEST_EMAIL}" \
    -e TEST_PASSWORD="${TEST_PASSWORD}" \
    test-load-login.js
}

# ── Entry point ───────────────────────────────────────────────────────────────
case "${1}" in
  spike) run_spike ;;
  soak)  run_soak  ;;
  load)  run_load  ;;
  all)
    run_spike
    echo "Sleeping 30s before next test..."
    sleep 30
    run_soak
    echo "Sleeping 30s before next test..."
    sleep 30
    run_load
    ;;
  *)
    echo "Usage: $0 {spike|soak|load|all}"
    echo ""
    echo "  spike  — burst traffic at health endpoints (~1.5 min)"
    echo "  soak   — steady DB load via /ready/ (~13 min)"
    echo "  load   — full login flow with session auth (~14 min)"
    echo "  all    — run all three in sequence"
    exit 1
    ;;
esac
