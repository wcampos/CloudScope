# CloudScope – Improvement Plan

This document outlines findings from reviewing the application (API, UI, and their interactions) and a prioritized plan to fix bugs, align API–UI contracts, and improve UX.

---

## 1. Current Architecture Summary

- **API service** (port 5001 → 5000): Flask-RESTX, PostgreSQL, exposes `/api/profiles`, `/api/resources`, `/api/profiles/parse`, activate/deactivate, `/health`.
- **UI service** (port 8001 → 8000): Flask, talks to API via `API_BASE_URL`, uses Redis for resource cache, serves Jinja templates and static assets.
- **Root `app.py`**: Monolithic Flask app (DB + templates); not used when running via docker-compose (api + ui).

Improvements below focus on the **API + UI** setup and **hitting the API** correctly from the UI.

---

## 2. API–UI Contract Issues (Fix First)

### 2.1 Profile creation (POST /api/profiles)

**Problem:**  
UI sends full form data: `name`, `custom_name`, `aws_access_key_id`, `aws_secret_access_key`, `aws_region`, `role_type`, `role_name`, `direct_session_token`, `aws_session_token`.  
API does `AWSProfile(**data)`, but the model has no `role_type`, `role_name`, or `direct_session_token` → creation fails.

**Fix:**

- **Option A (recommended):** In the API, accept the same form-like payload and resolve `aws_session_token` from `role_type` / `role_name` / `direct_session_token` / `aws_session_token` (mirror logic from root `app.py`), then create the profile with only model fields.
- **Option B:** In the UI, resolve role/session token before calling the API and send only model fields (name, custom_name, aws_access_key_id, aws_secret_access_key, aws_region, aws_session_token).

### 2.2 Profile GET response – do not expose secrets

**Problem:**  
API profile model/serialization includes `aws_access_key_id` and `aws_secret_access_key` in responses. That is a security risk.

**Fix:**

- Exclude or mask `aws_access_key_id` and `aws_secret_access_key` in all profile GET/list responses (e.g. custom serializer or a safe `to_dict()` that omits/masks these fields).
- Ensure API docs (Flask-RESTX) do not show secret fields as required in responses.

### 2.3 UI calls API with wrong content type for forms

**Problem:**  
UI uses `api_request('POST', '/api/profiles', json=request.form.to_dict())`. Form values are strings; API may expect correct types (e.g. booleans). Empty strings for optional fields can also cause issues.

**Fix:**

- Normalize payload in UI before sending (e.g. drop empty strings, convert booleans) or have API accept form-like JSON and coerce types.
- Keep using JSON for API; ensure required fields are always sent and optional ones are omitted or null when empty.

### 2.4 Health check response format

**Problem:**  
UI `/health` returns a plain dict. For consistency and for load balancers/probes, it should return JSON with a stable shape and correct status code.

**Fix:**

- Use `jsonify(...)` and explicit status codes (e.g. 200 for healthy, 503 when API is unreachable).
- Document the health response shape (e.g. `status`, `api_status`, `timestamp`) so frontends and infra can rely on it.

---

## 3. Missing UI Routes and Data

### 3.1 GET /profiles/<id> (for edit modal)

**Problem:**  
Profiles page edit modal does `fetch(\`/profiles/${profileId}\`)`. The UI app has no GET `/profiles/<id>` route, so the request 404s and the edit form cannot be filled.

**Fix:**

- Add a UI route, e.g. `GET /profiles/<int:profile_id>`, that proxies to `GET /api/profiles/<id>` and returns JSON (with secrets stripped or masked if the API still returns them until 2.2 is done).
- Alternatively, have the edit modal call the API directly from the browser only if the UI exposes a CORS-safe way or a same-origin proxy; the proxy approach is simpler and keeps API base URL server-side.

### 3.2 Index page – active profile

**Problem:**  
Index template expects `active_profile` (e.g. “Currently using profile: …”). UI index route does not pass it, so the block is always “No Active AWS Profile” or broken.

**Fix:**

- In the index route, call `GET /api/profiles`, find the active profile (e.g. `is_active=True`), and pass it to the template as `active_profile`.
- If the API does not mark active in list response, add `is_active` to profile list response and use it in the UI.

### 3.3 Resource shortcuts (/ec2, /s3, /networks, etc.)

**Problem:**  
Index and possibly other templates link to `/ec2`, `/s3`, `/networks`, `/lambda`, `/dynamodb`, `/alb`, `/sgs`, etc. The UI app does not define these routes, so they 404 when using the API+UI stack.

**Fix:**

- Add UI routes for these paths that redirect to the dashboard with the appropriate `view` (e.g. `/ec2` → `dashboard?view=compute`, `/s3` → `dashboard?view=storage`, `/networks` or `/sgs` → `dashboard?view=network`, etc.) so existing links work and “hit” the same dashboard that uses the API resources.

### 3.4 Settings page context

**Problem:**  
Settings template uses `version`, `flask_env`, `debug_mode`, `db_host`, `db_name`, `db_port`. The UI `settings()` route renders the template with no context, so these variables are undefined.

**Fix:**

- Either:
  - Fetch version/config from the API if you add a small “system” or “config” endpoint (e.g. version, env), and pass that into the template, or
  - In the UI, pass at least `version` (from env or package), `flask_env`, `debug_mode`, and if needed placeholder or minimal DB info (UI may not have DB access; then show “N/A” or “Managed by API”).
- Ensure the template does not assume DB connection in the UI; only show what the UI service actually knows.

---

## 4. Missing or Wrong Templates

### 4.1 add_profile and edit_profile templates

**Problem:**  
- On POST to `add_profile`, the UI renders `add_profile.html.j2` on error; that template does not exist → 404/500.
- On GET `edit_profile(profile_id)` the UI renders `edit_profile.html.j2`; that template does not exist.

**Fix:**

- **add_profile:** Either create a minimal `add_profile.html.j2` (e.g. same form as in profiles page) or, better, on validation/API error redirect back to `profiles` with a flash message and do not render a separate add template. That way one source of truth is the profiles page form.
- **edit_profile:** The profiles page already has an edit modal; the edit flow should be “GET profile JSON → fill modal → POST to `/profiles/<id>/edit`”. So:
  - Remove or avoid GET `edit_profile` that renders `edit_profile.html.j2`; implement GET only as a JSON endpoint (see 3.1) for the modal.
  - Ensure POST `/profiles/<id>/edit` continues to redirect to profiles with a flash message.

### 4.2 Static CSS path in some templates

**Problem:**  
Templates such as `sgs.html.j2`, `s3.html.j2`, `rds.html.j2`, `networks.html.j2`, `lambda.html.j2`, `ec2.html.j2`, `dynamodb.html.j2`, `alb.html.j2` reference `url_for('static', filename='styles/styles.css')`, but under `ui/static` there is only `css/style.css` (no `styles/` directory). Those pages will have broken or missing CSS if they are ever used.

**Fix:**

- Use the same layout as base (e.g. extend `base.html.j2` and use `static/css/style.css`) or add a `styles` directory and a `styles.css` that either mirrors or imports the main style. Prefer extending base so one CSS is used everywhere.

---

## 5. UI/UX Improvements

### 5.1 Dashboard loading and fallback

**Problem:**  
Dashboard shows a loading spinner and hides the resources container; JS then replaces the container content with `renderResources(...)`. If JS fails or is disabled, the user may see loading forever and no server-rendered fallback.

**Fix:**

- Either keep a server-rendered block inside the resources container as fallback (so without JS the user still sees data), or ensure the spinner is hidden and a message is shown after a timeout if no JS runs.
- Prefer one source of truth: e.g. server-rendered first, then enhance with JS (e.g. DataTables, refresh button) so the page works without JS.

### 5.2 Refresh cache button and icons

**Problem:**  
Dashboard “Refresh Cache” button uses `<i class="fas fa-sync-alt"></i>`. Font Awesome is not included in `base.html.j2`, so the icon does not show.

**Fix:**

- Add Font Awesome (e.g. CDN) in `base.html.j2`, or replace the icon with a Bootstrap icon or an inline SVG/emoji so the button is clear without extra dependencies.

### 5.3 Alerts and feedback

**Problem:**  
`main.js` auto-hides all `.alert` elements after 5 seconds. That can hide important errors or success messages too quickly.

**Fix:**

- Consider auto-hiding only success/info alerts, and keeping errors visible until dismissed, or increase the delay for error alerts.
- Ensure API errors from the UI (e.g. profile create/edit, set active, parse credentials) are shown as flash messages and that the user can read them before they disappear.

### 5.4 Set active profile form

**Problem:**  
Profiles page uses a single form for “Set Active Profile” with radio buttons; the button submits the form. If no profile is selected, the UI could show a clear validation message instead of relying on the user noticing nothing happened.

**Fix:**

- Keep the existing client-side check (“Please select a profile first”); optionally add a server-side check and flash message if `profile_id` is missing so behavior is consistent even without JS.

---

## 6. API Consistency and Dashboard Filtering

### 6.1 Resource keys vs view categories

**Problem:**  
Dashboard view filter uses categories like `compute`, `storage`, `network`, `services` and maps them to service name substrings (e.g. `ec2`, `lambda`, `s3`, `vpc`). If the API resource keys from `get_all_resources()` use different names (e.g. “EC2 Instances” vs “ec2”), filtering may miss them or be inconsistent.

**Fix:**

- In the API, document the exact resource keys returned (e.g. in `aws_classes.py`: keys of the dict returned by `get_all_resources()`).
- In the UI, align the `service_categories` mapping (and any server-side filter in the dashboard route) with those keys so “Compute”, “Storage”, “Network”, “Services” show the expected resources. Adjust string matching (e.g. case-insensitive, or by exact key) as needed.

### 6.2 Dashboard filter on UI vs API

**Problem:**  
Filtering by view is done in the UI (server-side in the dashboard route and again in client-side JS). If the API supported a `view` or `category` query param, the API could return only the needed data and the UI would stay simple.

**Fix (optional):**

- Add optional query params to `GET /api/resources`, e.g. `?view=compute|storage|network|services`, and implement filtering in the API so the UI just passes the param through. This reduces duplication and keeps filtering logic in one place.

---

## 7. Suggested Implementation Order

1. **API–UI contract (critical)**  
   - Fix profile creation (2.1): API accepts form-like payload and resolves `aws_session_token`; or UI resolves and sends only model fields.  
   - Stop exposing secrets in profile GET (2.2).  
   - Add GET `/profiles/<id>` in UI (3.1) and wire edit modal to it.

2. **Broken flows and pages**  
   - Index: pass `active_profile` (3.2).  
   - Settings: pass required template variables (3.4).  
   - Add redirects for /ec2, /s3, etc. (3.3).  
   - Fix add_profile/edit_profile error paths and missing templates (4.1).  
   - Fix CSS path in standalone templates (4.2).

3. **UX and robustness**  
   - Dashboard fallback when JS fails (5.1).  
   - Icons/Font Awesome or replacement (5.2).  
   - Health response format (2.4).  
   - Alert auto-hide behavior (5.3).

4. **Optional**  
   - Optional `view` param on `/api/resources` (6.2).  
   - Align dashboard filter keys with API resource keys (6.1).

---

## 8. Quick Reference – UI Routes That Should Hit the API

| UI route / action          | Intended API call / behavior |
|----------------------------|------------------------------|
| Dashboard load             | GET /api/resources (or cached), GET /api/profiles for context if needed |
| Dashboard refresh          | POST /api/resources/refresh then reload or GET /api/resources |
| Profiles list             | GET /api/profiles |
| Add profile (submit)       | POST /api/profiles (with payload aligned to 2.1) |
| Edit profile (load modal)  | GET /api/profiles/<id> (via new UI proxy in 3.1) |
| Edit profile (save)        | PUT /api/profiles/<id> |
| Delete profile             | DELETE /api/profiles/<id> |
| Set active profile         | PUT /api/profiles/deactivate_all, then PUT /api/profiles/<id>/activate |
| Parse credentials          | POST /api/profiles/parse |
| Index (active profile)     | GET /api/profiles, use active in template (3.2) |
| Health                     | UI /health calls GET /health on API and returns JSON (2.4) |

Ensuring these routes and actions correctly hit the API and handle errors will fix the main “API interacts” (and PPA/API) behavior and make the UIs consistent and predictable.
