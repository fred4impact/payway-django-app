import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * SOAK TEST — /ready/ (DB connectivity)
 *
 * Purpose: Hold steady low load for an extended period to surface
 * DB connection exhaustion, memory leaks, or Postgres degrading over
 * time inside Docker.
 *
 * Env:
 *   BASE_URL  - default: http://localhost
 *
 * Run (Docker + Prometheus):
 *   K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
 *   k6 run --out experimental-prometheus-rw test-soak-ready.js
 *
 * Run (Cloud — swap in cloud options below first):
 *   K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
 *   k6 run --out experimental-prometheus-rw \
 *          -e BASE_URL=https://your-cloud-url test-soak-ready.js
 */

// ─── Docker defaults (conservative) ────────────────────────────────────────
export const options = {
  stages: [
    { duration: '2m', target: 3 },   // ramp up to 3 VUs
    { duration: '10m', target: 3 },  // hold — main soak window
    { duration: '1m', target: 0 },   // ramp down
  ],
  thresholds: {
    checks: ['rate>0.95'],                      // 95%+ checks must pass
    http_req_failed: ['rate<0.05'],             // <5% errors
    http_req_duration: ['p(95)<800'],           // 95th percentile under 800ms
  },
};

// ─── Cloud options (uncomment + comment out Docker options above) ───────────
// export const options = {
//   stages: [
//     { duration: '2m',  target: 20 },   // ramp up
//     { duration: '30m', target: 20 },   // hold — extended soak
//     { duration: '2m',  target: 0  },   // ramp down
//   ],
//   thresholds: {
//     checks: ['rate>0.95'],
//     http_req_failed: ['rate<0.05'],
//     http_req_duration: ['p(95)<600'],
//   },
// };

const BASE = (__ENV.BASE_URL || 'http://localhost').replace(/\/$/, '');

export default function main() {
  const res = http.get(`${BASE}/ready/`);

  check(res, {
    // 200 = DB up, 503 = DB down — both are valid responses (not a network fail)
    'ready reachable':       (r) => r.status === 200 || r.status === 503,
    'ready DB up':           (r) => r.status === 200,
    'ready has status field':(r) => {
      try { return typeof r.json().status === 'string'; } catch { return false; }
    },
  });

  // Slow cadence — this is a soak, not a hammer
  sleep(2);
}
