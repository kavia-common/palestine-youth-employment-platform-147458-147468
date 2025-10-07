# Backend Health and Connectivity Verification

This backend exposes two health endpoints that validate database connectivity with automatic fallback and report CORS configuration.

Endpoints:
- GET /
- GET /health

Behavior:
- Performs a SELECT 1 using DATABASE_URL (sslmode=require enforced).
- If the first attempt fails, automatically retries using DIRECT_URL if present.
- Returns JSON including:
  - status: "ok" or "degraded"
  - env: application environment
  - sslmode: effective sslmode (should be "require")
  - has_database_url: boolean
  - has_direct_url: boolean
  - tried_direct: boolean indicating whether DIRECT_URL fallback was attempted
  - dsn_preview: masked DSN (no password)
  - db_scheme: normalized scheme (postgresql+psycopg)
  - db_connection: masked connection diagnostics (source, scheme, sslmode)
  - allow_origins: currently effective CORS origins

CORS:
- In development, http://localhost:3000 is included in allow_origins to enable frontend access.
- You can verify via GET /api/debug/cors

How to verify:
1) Check root health:
   curl -sS <BASE_URL>/
   Expected: status field "ok" when DB is reachable. sslmode should be "require".

2) Check health endpoint:
   curl -sS <BASE_URL>/health
   Expected fields as above, including tried_direct=false (or true if fallback used).

3) Check CORS:
   curl -sS <BASE_URL>/api/debug/cors
   Ensure http://localhost:3000 is present in development.

Notes:
- Ensure .env has DATABASE_URL configured. DIRECT_URL is optional but recommended for fallback.
- The backend normalizes URLs to postgresql+psycopg and enforces sslmode=require if unspecified.
- Sensitive values are masked in responses and logs.

Live verification snapshot (latest):
- GET / returned HTTP 200 with payload status="degraded"; message indicated psycopg.OperationalError: [Errno -2] Name or service not known.
- GET /health returned identical degraded payload.
- CORS allow_origins included ["*", "http://localhost:3000"].
- sslmode reported as "require".

After patch:
- Engine initialization attempts both DATABASE_URL and DIRECT_URL within the same call; health endpoints will succeed when either is valid.
- Diagnostics now populate scheme and dsn_preview from env even if engine init fails, to avoid "unparseable" where possible.
