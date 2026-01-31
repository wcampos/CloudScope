# Environment and configuration

## Overview

| Component   | Config / env                          | Notes |
|------------|----------------------------------------|-------|
| **API**    | FastAPI (main.py), uvicorn port 5000   | No Flask. `DATABASE_URL` required. |
| **Frontend** | Vite dev 5173, Docker nginx 80 → 3000 | Proxy: `/api`, `/health` → API. |
| **Database** | PostgreSQL 16, user `cloudscope`, DB `cloudscope` | Docker: `db:5432`, local: `localhost:5432`. |
| **Migrations** | Alembic, same `DATABASE_URL` as API   | Run in Docker via `migrations` service. |

---

## Environment variables

### Root / API

| Variable       | Where used   | Docker value (compose) | Local dev example |
|----------------|-------------|------------------------|-------------------|
| `DATABASE_URL` | api, migrations | `postgresql://cloudscope:cloudscope@db:5432/cloudscope` | `postgresql://cloudscope:cloudscope@localhost:5432/cloudscope` |

- **Docker:** Set in `docker-compose.yml` for `api` and `migrations`. No `.env` required.
- **Local API:** Copy `api/.env.example` to `api/.env` and set `DATABASE_URL` for your DB (e.g. DB in Docker → `localhost:5432`).

### Docker API healthcheck (optional)

Set in `.env` next to `docker-compose.yml` to tune the API container healthcheck (avoids flapping unhealthy):

| Variable | Default | Purpose |
|----------|---------|---------|
| `HEALTHCHECK_INTERVAL` | 60 | Seconds between checks. |
| `HEALTHCHECK_TIMEOUT` | 15 | Seconds to wait per check. |
| `HEALTHCHECK_RETRIES` | 3 | Failures before marking unhealthy. |
| `HEALTHCHECK_START_PERIOD` | 30 | Seconds before first failure counts. |

### Frontend

| Variable         | Where used | Purpose |
|------------------|-----------|---------|
| `VITE_API_URL`   | api/client.ts | Base URL for API. **Empty** = same-origin (use proxy). Set only if API is on another host/port and no proxy (e.g. `http://localhost:5001`). |
| `VITE_APP_VERSION` | Optional | App version string. |
| `VITE_HEALTH_CHECK_INTERVAL_MINUTES` | 2 | Settings page: auto-refresh health checks every N minutes (1–60). |

- **Dev (npm run dev):** Leave `VITE_API_URL` unset so Vite proxies `/api` and `/health` to `http://localhost:5001`. Run API on port **5001**.
- **Docker:** Frontend is built without env; nginx proxies `/api` and `/health` to `http://api:5000`.

---

## Ports and URLs

| Context        | Frontend      | API (reachable at) | DB (reachable at) |
|----------------|---------------|--------------------|-------------------|
| **Docker**     | http://localhost:3000 | http://api:5000 (internal), http://localhost:5001 (host) | db:5432 (internal), localhost:5432 (host) |
| **Local dev**  | http://localhost:5173 | http://localhost:5001 (Vite proxy target) | localhost:5432 |

---

## Quick checks

1. **API reachable**
   - Docker: `curl -s http://localhost:5001/health`
   - From frontend container: nginx proxies to `http://api:5000/health`.

2. **Database**
   - Docker: `docker compose exec db pg_isready -U cloudscope`
   - API/migrations use `DATABASE_URL`; must match DB user/db name (cloudscope/cloudscope).

3. **Profiles page “Network Error”**
   - Dev: Ensure API is running on port 5001 and Vite proxy is used (no `VITE_API_URL` or empty).
   - Docker: Ensure `api` service is up and healthy; frontend at 3000 uses nginx → api:5000.
