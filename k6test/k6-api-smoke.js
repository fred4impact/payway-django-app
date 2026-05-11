import http from 'k6/http';
import { check, group, sleep } from 'k6';

/**
 * Env:
 *   BASE_URL        - e.g. http://127.0.0.1:8000 (no trailing slash)
 *   SESSION_COOKIE  - optional; raw sessionid value for authenticated endpoints
 *   TEST_EMAIL      - optional; with TEST_PASSWORD, performs form login (no 2FA)
 *   TEST_PASSWORD   - optional
 *
 * See k6-test.md for usage.
 */
export const options = {
  scenarios: {
    smoke: {
      executor: 'per-vu-iterations',
      vus: 5,
      iterations: 4,
      maxDuration: '60s',
    },
  },
  thresholds: {
    checks: ['rate>0.85'],
    http_req_failed: ['rate<0.15'],
  },
};

const BASE = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function jsonPath(res, path) {
  try {
    const j = res.json();
    let cur = j;
    for (const p of path.split('.')) {
      cur = cur[p];
    }
    return cur;
  } catch {
    return undefined;
  }
}

export default function main() {
  group('operational (no auth)', () => {
    let res = http.get(`${BASE}/health/`);
    check(res, {
      'health status 200': (r) => r.status === 200,
      'health body UP': (r) => jsonPath(r, 'status') === 'UP',
    });

    res = http.get(`${BASE}/ready/`);
    check(res, {
      'ready reachable': (r) => r.status === 200 || r.status === 503,
      'ready JSON status': (r) =>
        r.status === 503 || jsonPath(r, 'status') === 'UP',
    });

    res = http.get(`${BASE}/actuator/health/`);
    check(res, {
      'actuator reachable': (r) => r.status === 200 || r.status === 503,
    });

    res = http.get(`${BASE}/actuator/health/liveness/`);
    check(res, { 'actuator liveness 200': (r) => r.status === 200 });

    res = http.get(`${BASE}/actuator/health/readiness/`);
    check(res, {
      'actuator readiness reachable': (r) => r.status === 200 || r.status === 503,
    });

    res = http.get(`${BASE}/api/`);
    check(res, {
      'api discovery 200': (r) => r.status === 200,
      'api discovery has json_apis': (r) => Array.isArray(jsonPath(r, 'json_apis')),
    });
  });

  const sessionCookie = __ENV.SESSION_COOKIE;
  if (sessionCookie) {
    group('authenticated (SESSION_COOKIE)', () => {
      const cookieHeader = { Cookie: `sessionid=${sessionCookie}` };

      let res = http.get(`${BASE}/auth/api/security/summary/`, {
        headers: cookieHeader,
      });
      check(res, {
        'security summary 200': (r) => r.status === 200,
        'security summary has score': (r) =>
          typeof jsonPath(r, 'security_score') === 'number',
      });

      res = http.get(`${BASE}/auth/api/security/events/`, {
        headers: cookieHeader,
      });
      check(res, {
        'security events 200': (r) => r.status === 200,
        'security events array': (r) => Array.isArray(jsonPath(r, 'events')),
      });

      res = http.get(`${BASE}/account/notifications/count/`, {
        headers: {
          ...cookieHeader,
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
      check(res, {
        'notifications count 200': (r) => r.status === 200,
        'notifications count field': (r) =>
          typeof jsonPath(r, 'count') === 'number',
      });
    });
  }

  const email = __ENV.TEST_EMAIL;
  const password = __ENV.TEST_PASSWORD;
  if (email && password && !sessionCookie) {
    group('login form then security JSON (no 2FA users only)', () => {
      const loginPage = http.get(`${BASE}/auth/login/`);
      check(loginPage, { 'login page 200': (r) => r.status === 200 });

      const m = loginPage.body.match(/name="csrfmiddlewaretoken" value="([^"]+)"/);
      if (!m) {
        return;
      }
      const csrftoken = m[1];
      const body = [
        `csrfmiddlewaretoken=${encodeURIComponent(csrftoken)}`,
        `email=${encodeURIComponent(email)}`,
        `password=${encodeURIComponent(password)}`,
      ].join('&');

      const loginRes = http.post(`${BASE}/auth/login/`, body, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Referer: `${BASE}/auth/login/`,
        },
      });

      check(loginRes, {
        'login POST redirect or ok': (r) =>
          r.status === 200 || r.status === 302,
      });

      const c = loginRes.cookies.sessionid;
      const sid = c && c[0] && c[0].value;
      if (!sid) {
        return;
      }

      const hdrs = { Cookie: `sessionid=${sid}` };
      const sum = http.get(`${BASE}/auth/api/security/summary/`, { headers: hdrs });
      check(sum, {
        'after login security summary 200': (r) => r.status === 200,
      });
    });
  }

  sleep(0.3);
}
