# Backend smoke tests

This document describes quick checks to validate Supabase migrations, DB connectivity, health endpoints, and CORS.

Prerequisites:
- .env configured (see .env.example), with a working DATABASE_URL pointing to Supabase Postgres.
- Optionally run migrations:
  chmod +x scripts/run_migrations.sh
  ./scripts/run_migrations.sh
  RUN_SEED=true ./scripts/run_migrations.sh

Checks:
1) Health endpoints
- GET / -> JSON with {"status": "ok"|"degraded", "env": "...", "message": "..."}
- GET /health -> Same payload as root, dedicated for probes

2) DB connectivity
- With .env set, backend attempts SELECT 1 during health checks.
- If DATABASE_URL is missing or invalid, response shows status "degraded" with guidance.
- SSL: The backend enforces sslmode=require by default for postgres URLs when not set.

3) CORS
- Set CORS_ORIGINS to http://localhost:3000 (for frontend dev server).
- Backend allows credentials, methods, and headers for those origins.

4) Key routes
- GET /api/analytics/counts -> returns counts for users, jobs, applications
- GET /api/cms/news -> returns published news (after seed)
- GET /api/jobs -> returns list of published jobs

5) Debug DB config (optional, non-prod)
- Set DEBUG_DB_CONFIG=true in .env to enable GET /api/debug/db-config.
- Call GET /api/debug/db-config -> verifies that DATABASE_URL is present, reports sslmode (should be "require" unless explicitly set), and shows a masked DSN preview.

Troubleshooting:
- DATABASE_URL invalid: Update .env and restart service.
- SSL issues with Supabase: Backend adds sslmode=require by default; if your environment needs a different setting (e.g., verify-full), append ?sslmode=verify-full to DATABASE_URL.
- CORS blocked in the browser console: Set CORS_ORIGINS to the exact Origin (scheme+host+port) of your frontend. For local React dev server, use http://localhost:3000
