# CloudScope – React UI

React SPA for CloudScope (AWS resource management). Built with Vite, TypeScript, React Router, TanStack Query, and Bootstrap.

## Prerequisites

- Node 18+
- API service running (e.g. `docker compose up api` or `make up` for API on port 5001)

## Development

```bash
npm install
npm run dev
```

Runs at http://localhost:5173. API requests are proxied to http://localhost:5001 (set in `vite.config.ts`).

## Build

```bash
npm run build
```

Output in `dist/`. Serve with any static host; in production, proxy `/api` and `/health` to the API service.

## Docker

From repo root:

```bash
docker compose --profile react up frontend
```

React app is served on port 3000; `/api` is proxied to the API service.

## Environment

- `VITE_API_URL` – API base URL (default: `''` for same-origin; set for different host).
- `VITE_APP_VERSION` – App version (optional).
