# PayWay k6 + Prometheus + Grafana — Setup Guide

## Folder structure

```
project-root/
├── docker-compose.yml               ← your existing file
├── monitoring/
│   ├── docker-compose.monitoring.yml  ← add these services to yours
│   ├── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/prometheus.yml
│       │   └── dashboards/default.yml
│       └── dashboards/
│           └── payway-k6.json
├── test-soak-ready.js
├── test-load-login.js
└── test-spike-health.js
```

---

## Step 1 — Merge docker-compose files

Copy the services from `monitoring/docker-compose.monitoring.yml` into
your existing `docker-compose.yml`, then add the `monitoring` network
to your Django/nginx service:

```yaml
services:
  web:          # or nginx — whatever your service is called
    networks:
      - default
      - monitoring   # ← add this
```

Then bring up the new services:

```bash
docker compose up -d prometheus grafana
```

Verify they're running:
- Prometheus: http://localhost:9090
- Grafana:    http://localhost:3000  (admin / admin)

---

## Step 2 — Confirm Prometheus is scraping

Open http://localhost:9090/targets — you should see the `k6` job listed
(it will be DOWN until you run a test — that's fine).

---

## Step 3 — Run a test with Prometheus output

All three tests use the same pattern:

```bash
# Spike test (fastest — run this first)
K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
k6 run --out experimental-prometheus-rw test-spike-health.js

# Soak test
K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
k6 run --out experimental-prometheus-rw test-soak-ready.js

# Load test (requires test account credentials)
K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
k6 run --out experimental-prometheus-rw \
       -e TEST_EMAIL=user@example.com \
       -e TEST_PASSWORD=secret \
       test-load-login.js
```

> k6 pushes metrics to Prometheus via remote-write on port 9090.
> No separate scrape endpoint needed with this approach.

---

## Step 4 — Open the Grafana dashboard

1. Go to http://localhost:3000
2. Login: admin / admin
3. Navigate to Dashboards → k6 Load Tests → **PayWay — k6 Load Tests**

The dashboard auto-refreshes every 5 seconds. Run a test and watch it live.

---

## Dashboard panels

| Panel | What it shows |
|-------|--------------|
| Check Pass Rate | % of k6 checks passing (target >85%) |
| HTTP Error Rate | % of failed HTTP requests (target <10%) |
| p95 Response Time | 95th percentile latency in ms |
| Active VUs | Virtual users currently running |
| Requests/sec | Throughput over last 30s |
| Duration Percentiles | p50 / p95 / p99 over time |
| Duration by URL | p95 broken down per endpoint |
| Request Phase Breakdown | connect / waiting (TTFB) / receiving / sending |
| Virtual Users | Active vs max VUs over test run |
| Iterations/sec | Test loop throughput |

---

## Thresholds at a glance

| Test | VUs (Docker) | VUs (Cloud) | Duration |
|------|-------------|-------------|----------|
| Spike | 2 → 20 → 2 | 5 → 100 → 5 | ~1.5 min |
| Soak  | 3 steady   | 20 steady   | ~13 min  |
| Load  | 5 → 10     | 25 → 50     | ~14 min  |
docker compose up -d prometheus grafana

```bash
K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
k6 run --out experimental-prometheus-rw test-auth-login.js
```