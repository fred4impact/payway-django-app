import http from 'k6/http';
import { check, group, sleep } from 'k6';

/**
 * SPIKE TEST — Health & discovery endpoints
 *
 * Purpose: Suddenly burst traffic at the health/liveness/readiness
 * and API discovery endpoints to verify the app stays stable and
 * nginx doesn't drop connections under sudden load. Fast to run —
 * good as a baseline before heavier tests.
 *
 * Env:
 *   BASE_URL  - default: http://localhost
 *
 * Run (Docker):
 *   k6 run test-spike-health.js
 *
 * Run (Cloud — swap in cloud options below first):
 *   k6 run -e BASE_URL=https://your-cloud-url test-spike-health.js
 */

// ─── Docker defaults (conservative) ────────────────────────────────────────
export const options = {
  stages: [
    { duration: '10s', target: 2  },  // warm up — tiny baseline
    { duration: '10s', target: 20 },  // spike — sudden jump
    { duration: '30s', target: 20 },  // hold the spike
    { duration: '10s', target: 2  },  // drop back
    { duration: '10s', target: 0  },  // ramp down
  ],
  thresholds: {
    checks: ['rate>0.90'],
    http_req_failed: ['rate<0.10'],
    http_req_duration: ['p(95)<500'],  // health endpoints should be very fast
  },
};

// ─── Cloud options (uncomment + comment out Docker options above) ───────────
// export const options = {
//   stages: [
//     { duration: '10s', target: 5   },  // warm up
//     { duration: '15s', target: 100 },  // spike
//     { duration: '1m',  target: 100 },  // hold the spike
//     { duration: '15s', target: 5   },  // drop back
//     { duration: '10s', target: 0   },  // ramp down
//   ],
//   thresholds: {
//     checks: ['rate>0.90'],
//     http_req_failed: ['rate<0.10'],
//     http_req_duration: ['p(95)<400'],
//   },
// };

const BASE = (__ENV.BASE_URL || 'http://localhost').replace(/\/$/, '');

function jsonPath(res, path) {
  try {
    let cur = res.json();
    for (const p of path.split('.')) { cur = cur[p]; }
    return cur;
  } catch { return undefined; }
}

export default function main() {
  // ── Liveness (no DB) ──────────────────────────────────────────────────
  group('liveness - /health/', () => {
    const res = http.get(`${BASE}/health/`);
    check(res, {
      'health 200':    (r) => r.status === 200,
      'health UP':     (r) => jsonPath(r, 'status') === 'UP',
    });
  });

  group('actuator liveness', () => {
    const res = http.get(`${BASE}/actuator/health/liveness/`);
    check(res, {
      'actuator liveness 200': (r) => r.status === 200,
    });
  });

  // ── Readiness (hits DB — watch for 503s under spike) ──────────────────
  group('readiness - /ready/', () => {
    const res = http.get(`${BASE}/ready/`);
    check(res, {
      'ready reachable':  (r) => r.status === 200 || r.status === 503,
      'ready DB up':      (r) => r.status === 200,
    });
  });

  group('actuator readiness', () => {
    const res = http.get(`${BASE}/actuator/health/readiness/`);
    check(res, {
      'actuator readiness reachable': (r) => r.status === 200 || r.status === 503,
    });
  });

  // ── Actuator aggregate ─────────────────────────────────────────────────
  group('actuator aggregate - /actuator/health/', () => {
    const res = http.get(`${BASE}/actuator/health/`);
    check(res, {
      'actuator aggregate reachable': (r) => r.status === 200 || r.status === 503,
    });
  });

  // ── API discovery ──────────────────────────────────────────────────────
  group('api discovery - /api/', () => {
    const res = http.get(`${BASE}/api/`);
    check(res, {
      'api discovery 200':          (r) => r.status === 200,
      'api discovery has json_apis':(r) => Array.isArray(jsonPath(r, 'json_apis')),
    });
  });

  sleep(0.1); // minimal sleep — spike test keeps pressure high
}