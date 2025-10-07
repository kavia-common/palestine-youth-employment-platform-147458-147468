# YEP Job Matching Backend (FastAPI)

This service provides the backend API for the AI-Driven Job Matching Platform. It integrates with Supabase Postgres and exposes REST endpoints for jobs, users, search, matching, notifications, analytics, and admin.

Quick start
- Install dependencies:
  pip install -r requirements.txt
- Configure environment (.env). See .env.example for all variables.
  - DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
    Note: The backend enforces sslmode=require by default if not present.
  - CORS_ORIGINS=http://localhost:3000 (for local frontend dev)
  - SUPABASE_URL, SUPABASE_SERVICE_KEY/ANON_KEY, SUPABASE_JWT_SECRET as provided by orchestrator (do not hardcode real values)
- Run server:
  uvicorn src.api.main:app --host 0.0.0.0 --port 8000
- Health checks:
  - GET /           -> {"status": "ok"|"degraded", "env": "...", "message": "..."}
  - GET /health     -> same payload, intended for probes

Database connectivity
- On startup or when hitting / or /health the backend performs a basic "SELECT 1".
- The connection string is normalized to:
  - Use the psycopg v3 driver for SQLAlchemy (postgresql+psycopg://)
  - Append sslmode=require if not already present
- If DATABASE_URL is missing or invalid, endpoints will return status="degraded" with a helpful message.

CORS
- Set CORS_ORIGINS to the exact Origin(s) of your frontend. For local React dev:
  CORS_ORIGINS=http://localhost:3000
- The backend allows credentials, methods, and headers for those origins.
- For debugging during development you can set "*" (not recommended for production).

Migrations
- Use scripts/run_migrations.sh to apply SQL in docs/database in order.
- Seed development data by setting RUN_SEED=true when invoking the script.
- Ensure .env has a working DATABASE_URL before running migrations.

Troubleshooting
- Health shows degraded and mentions DB not reachable or misconfigured
  Causes:
    - DATABASE_URL contains special characters (e.g., '@', '[', ']') in the password which can break strict URL parsing.
    - Network/connectivity issues or invalid credentials.
  Actions:
    1) Ensure requirements installed (psycopg[binary] is included).
    2) Ensure DATABASE_URL uses postgres or postgresql scheme; the backend rewrites to postgresql+psycopg internally and enforces sslmode=require by default.
    3) If your password contains special characters, leave it as-is; the backend handles normalization without strict parsing.
    4) Verify connectivity and credentials to your Supabase Postgres.
- CORS blocked in browser:
  Ensure CORS_ORIGINS contains the exact Origin (scheme+host+port) or use "*" for dev.
- See docs/SMOKE_TESTS.md for a focused smoke test checklist (health, DB connectivity, CORS, and key routes).

OpenAPI
- Visit /docs for Swagger UI and /openapi.json for the schema.
- To regenerate interfaces/openapi.json locally:
  python -m src.api.generate_openapi
