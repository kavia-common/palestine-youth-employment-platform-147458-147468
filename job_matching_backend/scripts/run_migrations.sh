#!/usr/bin/env bash
# Run Supabase/Postgres migrations for the Job Matching Backend.
# - Parses DATABASE_URL from .env to discrete PG* vars to avoid URI parsing issues (special chars)
# - Applies migrations 001..009, storage_policies.sql, realtime_enable.sql
# - Optionally applies seed_dev.sql when RUN_SEED=true
# Usage:
#   chmod +x scripts/run_migrations.sh
#   ./scripts/run_migrations.sh             # runs all core migrations
#   RUN_SEED=true ./scripts/run_migrations.sh  # also runs development seed data

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found in $(pwd). Please ensure environment variables are configured." >&2
  exit 1
fi

# Load .env (non-exported vars too)
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set in $ENV_FILE" >&2
  exit 1
fi

# Parse DATABASE_URL to discrete psql env vars to avoid issues with special characters and query params.
# Expected format: postgresql://user:password@host:port/dbname[?params]
parse_output="$(python3 - <<'PY'
import os, re, sys
url = os.getenv("DATABASE_URL","").strip()
m = re.match(r"^postgresql://([^:]+):([^@]+)@([^:/]+):([0-9]+)/([^?]+)", url)
if not m:
    print(f"ERROR: Invalid DATABASE_URL format: {url}", file=sys.stderr)
    sys.exit(2)
user, pw, host, port, db = m.groups()
print(f"PGUSER={user}")
print(f"PGPASSWORD={pw}")
print(f"PGHOST={host}")
print(f"PGPORT={port}")
print(f"PGDATABASE={db}")
PY
)" || exit $?

# Export parsed values
# shellcheck disable=SC2046
export $(echo "$parse_output" | cut -d= -f1)
# shellcheck disable=SC2046
eval export $(echo "$parse_output" | sed 's/^/"/; s/$/"/' | sed 's/=/="/; s/$/"/')

echo "Connecting to: ${PGUSER}@${PGHOST}:${PGPORT}/${PGDATABASE}"

PSQL="psql -v ON_ERROR_STOP=1"

# Paths
DB_DIR="docs/database"
MIG_DIR="$DB_DIR/migrations"

apply_sql() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "ERROR: SQL file not found: $file" >&2
    exit 3
  fi
  echo "Applying: $file"
  $PSQL -f "$file"
}

# Apply migrations in order
apply_sql "$MIG_DIR/001_init.sql"
apply_sql "$MIG_DIR/002_profiles.sql"
apply_sql "$MIG_DIR/003_jobs.sql"
apply_sql "$MIG_DIR/004_interactions.sql"
apply_sql "$MIG_DIR/005_embeddings_match.sql"
apply_sql "$MIG_DIR/006_integrations.sql"
apply_sql "$MIG_DIR/007_notifications_cms.sql"
apply_sql "$MIG_DIR/008_analytics.sql"
apply_sql "$MIG_DIR/009_policies_rls.sql"

# Storage and Realtime
apply_sql "$DB_DIR/storage_policies.sql"
apply_sql "$DB_DIR/realtime_enable.sql"

# Optional seed (development only)
if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "RUN_SEED=true -> Applying development seed data"
  apply_sql "$DB_DIR/seed_dev.sql"
else
  echo "Skipping seed_dev.sql (set RUN_SEED=true to enable)"
fi

echo "Migrations complete."
