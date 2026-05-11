import http from 'k6/http';
import { check, group, sleep } from 'k6';

/**
 * LOAD TEST — Login flow → Security summary → Notifications count
 *
 * Purpose: Simulate realistic concurrent users doing the full auth
 * journey: fetch login page (CSRF) → POST credentials → call security
 * JSON → check notifications. Tests session handling and DB under
 * sustained load.
 *
 * NOTE: Only works for accounts with NO 2FA enabled.
 *
 * Env:
 *   BASE_URL       - default: http://localhost
 *   TEST_EMAIL     - login email (required)
 *   TEST_PASSWORD  - login password (required)
 *
 * Run (Docker + Prometheus):
 *   K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
 *   k6 run --out experimental-prometheus-rw \
 *          -e TEST_EMAIL=user@example.com -e TEST_PASSWORD=secret \
 *          test-load-login.js
 *
 * Run (Cloud — swap in cloud options below first):
 *   K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
 *   k6 run --out experimental-prometheus-rw \
 *          -e BASE_URL=https://your-cloud-url \
 *          -e TEST_EMAIL=user@example.com \
 *          -e TEST_PASSWORD=secret \
 *          test-load-login.js
 */

// ─── Docker defaults (conservative) ────────────────────────────────────────
export const options = {
  stages: [
    { duration: '1m', target: 5  },  // ramp up to 5 VUs
    { duration: '5m', target: 5  },  // hold steady
    { duration: '2m', target: 10 },  // step up to 10 VUs
    { duration: '5m', target: 10 },  // hold steady
    { duration: '1m', target: 0  },  // ramp down
  ],
  thresholds: {
    checks: ['rate>0.90'],
    http_req_failed: ['rate<0.10'],
    http_req_duration: ['p(95)<2000'],  // login form can be slower
  },
};

// ─── Cloud options (uncomment + comment out Docker options above) ───────────
// export const options = {
//   stages: [
//     { duration: '2m',  target: 25  },  // ramp up
//     { duration: '8m',  target: 25  },  // hold
//     { duration: '2m',  target: 50  },  // step up
//     { duration: '8m',  target: 50  },  // hold
//     { duration: '2m',  target: 0   },  // ramp down
//   ],
//   thresholds: {
//     checks: ['rate>0.90'],
//     http_req_failed: ['rate<0.10'],
//     http_req_duration: ['p(95)<1500'],
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
  const email    = __ENV.TEST_EMAIL;
  const password = __ENV.TEST_PASSWORD;

  if (!email || !password) {
    console.error('TEST_EMAIL and TEST_PASSWORD are required.');
    return;
  }

  // ── Step 1: Fetch login page & extract CSRF token ──────────────────────
  group('1 - fetch login page', () => {
    const loginPage = http.get(`${BASE}/auth/login/`);
    check(loginPage, { 'login page 200': (r) => r.status === 200 });
  });

  const loginPage = http.get(`${BASE}/auth/login/`);
  const m = loginPage.body.match(/name="csrfmiddlewaretoken" value="([^"]+)"/);
  if (!m) {
    console.error('Could not extract CSRF token — skipping iteration');
    return;
  }
  const csrftoken = m[1];

  sleep(0.5); // brief pause — simulates user typing

  // ── Step 2: POST credentials ───────────────────────────────────────────
  let sessionId;
  group('2 - login POST', () => {
    const body = [
      `csrfmiddlewaretoken=${encodeURIComponent(csrftoken)}`,
      `email=${encodeURIComponent(email)}`,
      `password=${encodeURIComponent(password)}`,
    ].join('&');

    const loginRes = http.post(`${BASE}/auth/login/`, body, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': `${BASE}/auth/login/`,
      },
    });

    check(loginRes, {
      'login POST succeeds':    (r) => r.status === 200 || r.status === 302,
      'session cookie returned': (r) => {
        const c = r.cookies.sessionid;
        return !!(c && c[0] && c[0].value);
      },
    });

    const c = loginRes.cookies.sessionid;
    sessionId = c && c[0] && c[0].value;
  });

  if (!sessionId) {
    console.error('No sessionid cookie — login failed or 2FA is active');
    return;
  }

  sleep(0.5);

  // ── Step 3: Security summary ───────────────────────────────────────────
  group('3 - security summary', () => {
    const res = http.get(`${BASE}/auth/api/security/summary/`, {
      headers: { Cookie: `sessionid=${sessionId}` },
    });
    check(res, {
      'security summary 200':       (r) => r.status === 200,
      'security summary has score': (r) => typeof jsonPath(r, 'security_score') === 'number',
      'account not locked':         (r) => jsonPath(r, 'is_locked') === false,
    });
  });

  sleep(0.3);

  // ── Step 4: Security events ────────────────────────────────────────────
  group('4 - security events', () => {
    const res = http.get(`${BASE}/auth/api/security/events/`, {
      headers: { Cookie: `sessionid=${sessionId}` },
    });
    check(res, {
      'security events 200':   (r) => r.status === 200,
      'security events array': (r) => Array.isArray(jsonPath(r, 'events')),
    });
  });

  sleep(0.3);

  // ── Step 5: Notifications count (AJAX) ────────────────────────────────
  group('5 - notifications count', () => {
    const res = http.get(`${BASE}/account/notifications/count/`, {
      headers: {
        'Cookie': `sessionid=${sessionId}`,
        'X-Requested-With': 'XMLHttpRequest',
      },
    });
    check(res, {
      'notifications count 200':   (r) => r.status === 200,
      'notifications count field': (r) => typeof jsonPath(r, 'count') === 'number',
    });
  });

  sleep(1); // simulate user reading the page
}
