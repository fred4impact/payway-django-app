# PayWay Django — HTTP API and integration guide

This app is primarily a **server-rendered Django site**: most behavior is **HTML pages** plus **session authentication** (cookie). A small set of endpoints returns **JSON**, mainly for in-page AJAX and for **health/readiness** probes.

For a machine-readable index of JSON endpoints (with your deployment’s absolute URLs), call **`GET /api/`** on the running server.

---

## Base URL

| Environment | Example base |
|-------------|----------------|
| Local `runserver` | `http://127.0.0.1:8000` |
| Docker Compose (`web` direct) | `http://localhost:8000` |
| Docker Compose (nginx front) | `http://localhost` (paths may be proxied; use the URL that reaches Django) |
| Kubernetes | Your Service/Ingress URL for the Django workload |

All paths below are **relative** to that base (e.g. `/health/` → `http://127.0.0.1:8000/health/`).

---

## How to interact with “all” HTTP behavior

There are three layers:

1. **Operational JSON (no login)** — health and discovery.
2. **JSON over session** — `GET`/`POST` with the **`sessionid`** cookie; some responses require the **`X-Requested-With: XMLHttpRequest`** header (jQuery-style AJAX).
3. **Everything else** — **browser or HTTP client** following redirects, **HTML forms**, and **CSRF** on unsafe methods. There is **no separate REST/OpenAPI service** covering transfers, KYC, etc.; those flows are form- and template-driven.

To exercise the full product as a user: use the **browser** (or tools like Playwright) and log in at **`/auth/login/`**. To call the **JSON** pieces from scripts, use the session workflow in [Authenticated JSON calls](#authenticated-json-calls).

---

## Operational endpoints (JSON, no auth)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health/` | **Liveness**: process up; does **not** query the database. Use for Kubernetes `livenessProbe`. |
| GET | `/ready/` | **Readiness**: checks DB connectivity. **503** if DB unavailable. Use for `readinessProbe`. |
| GET | `/actuator/health/` | Spring Boot Actuator–style aggregate: `status` + `components.db`. **503** if DB down. |
| GET | `/actuator/health/liveness/` | Same as `/health/`. |
| GET | `/actuator/health/readiness/` | Same as `/ready/`. |
| GET | `/api/` | Discovery JSON: links to health URLs and list of JSON APIs. |

**Examples:**

```bash
curl -sS http://127.0.0.1:8000/health/
curl -sS http://127.0.0.1:8000/ready/
curl -sS http://127.0.0.1:8000/api/
```

---

## Authenticated JSON calls

### 1. Obtain a session

Log in through the normal login form ( **`POST /auth/login/`** ) with:

- Form fields: whatever your login template expects (typically **username** or **email** and **password** — inspect the login page or `userauths` forms).
- Header: fetch **`GET /auth/login/`** first and send the **`csrftoken`** cookie value as **`X-CSRFToken`** (and include **`Cookie:`** with `csrftoken` + later `sessionid`).

Or log in once in a browser and copy the **`sessionid`** (and `csrftoken` if needed) from dev tools into your client.

### 2. Security APIs (always JSON when authenticated)

| Method | Path | Response (shape) |
|--------|------|-------------------|
| GET | `/auth/api/security/summary/` | `security_score`, `failed_login_attempts`, `is_locked`, device/event counts |
| GET | `/auth/api/security/events/` | `events`: list of recent security log lines |

**Example (after you have `sessionid`):**

```bash
curl -sS -b "sessionid=YOUR_SESSION_ID" \
  http://127.0.0.1:8000/auth/api/security/summary/
```

### 3. Notification AJAX endpoints (JSON only with AJAX header)

These views return JSON **only** if the request includes **`X-Requested-With: XMLHttpRequest`**. Otherwise you get a redirect or a **400** JSON error.

| Method | Path | Notes |
|--------|------|--------|
| GET | `/account/notifications/count/` | Returns `count`, optional `latest_notification`. |
| GET | `/account/notification/<notification_id>/read/` | Marks read; JSON `{"status":"success"}` when AJAX. |

**Example:**

```bash
curl -sS -b "sessionid=YOUR_SESSION_ID" \
  -H "X-Requested-With: XMLHttpRequest" \
  http://127.0.0.1:8000/account/notifications/count/
```

### 4. Transfer fee calculator (JSON on POST)

| Method | Path | Body (typical) | Success JSON |
|--------|------|----------------|--------------|
| POST | `/account/fee-calculator/` | `amount`, `currency` (form fields) | `success`, `amount`, `fee`, `total_amount`, `currency`, … |

Requires login and valid **CSRF** for POST if CSRF middleware applies (same as browser forms).

---

## Application routes (HTML / forms, session)

These are the main user-facing URL namespaces. They are **not** JSON APIs unless noted above.

### Core (`/`)

| Path | Description |
|------|-------------|
| `/` | Home |
| `/dashboard/` | Dashboard (login required) |

### Auth (`/auth/`)

| Path | Description |
|------|-------------|
| `/auth/register/` | Registration |
| `/auth/login/` | Login |
| `/auth/logout/` | Logout |
| `/auth/2fa/...` | Two-factor setup, verify, backup codes |
| `/auth/security/...` | Security dashboard, logs, settings, devices |
| `/auth/api/security/summary/` | JSON (session) |
| `/auth/api/security/events/` | JSON (session) |

### Account (`/account/`)

| Path | Description |
|------|-------------|
| `/account/kyc/` | KYC submission |
| `/account/kyc/detail/` | KYC detail |
| `/account/info/` | Account info |
| `/account/search/` | Account search |
| `/account/transfer/` | Money transfer |
| `/account/request/create/`, `/account/requests/`, `/account/request/<id>/`, `.../settle/` | Payment requests |
| `/account/transactions/`, `/account/transaction/<id>/` | Transactions |
| `/account/notifications/`, `/account/notifications/count/`, `/account/notification/<id>/read/` | Notifications |
| `/account/cards/`, `/account/cards/add/`, `.../edit/`, `.../delete/`, `.../fund/`, `.../withdraw/` | Cards |
| `/account/international/`, `.../create/`, `.../<transfer_id>/` | International transfers |
| `/account/swift-search/` | SWIFT search (HTML) |
| `/account/currency-converter/` | Currency converter (HTML) |
| `/account/fee-calculator/` | Fee calculator (HTML + **JSON on POST**) |

### Admin

| Path | Description |
|------|-------------|
| `/admin/` | Django admin |

---

## Kubernetes probes (quick reference)

- **`livenessProbe.httpGet.path`**: `/health/` (or `/actuator/health/liveness/`)
- **`readinessProbe.httpGet.path`**: `/ready/` (or `/actuator/health/readiness/`)

Avoid using DB-dependent URLs for liveness only, so transient DB issues do not restart the container.

---

## Document history

| Date | Change |
|------|--------|
| 2026-05-10 | Added this guide: operational `/health/`, `/ready/`, `/actuator/health/*`, discovery `GET /api/`, authenticated JSON endpoints (security, notifications AJAX, fee calculator POST), and HTML route map. |
