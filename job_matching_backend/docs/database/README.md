# Supabase Database Setup

This directory contains SQL migrations and scripts to set up the database schema, Row Level Security (RLS), storage buckets/policies, realtime replication, and development seed data for the AI-Driven Job Matching Platform.

Contents:
- migrations/001_init.sql: Extensions (pgvector), base helpers, users table
- migrations/002_profiles.sql: job_seekers, employers, education, experience, skills, seeker_skills
- migrations/003_jobs.sql: jobs, job_skills, applications, preferences
- migrations/004_interactions.sql: notifications, CMS (news/faq), integrations, audit_logs
- migrations/005_embeddings_match.sql: seekers_embeddings, jobs_embeddings, matching helper
- migrations/006_integrations.sql: reserved for future integration objects
- migrations/007_notifications_cms.sql: realtime-oriented views and analytics_events
- migrations/008_analytics.sql: materialized views and analytics helpers
- migrations/009_policies_rls.sql: RLS policies for all tables/views
- storage_policies.sql: Storage buckets (resumes, logos, attachments) and policies
- realtime_enable.sql: Realtime publication entries for selected tables
- seed_dev.sql: Development seed data

Environment variables used by the backend/container:
- REACT_APP_SUPABASE_URL
- REACT_APP_SUPABASE_KEY
These must be provided by the orchestrator via .env; do not hardcode.

Execution Order (in Supabase SQL Editor or CLI):
1. migrations/001_init.sql
2. migrations/002_profiles.sql
3. migrations/003_jobs.sql
4. migrations/004_interactions.sql
5. migrations/005_embeddings_match.sql
6. migrations/006_integrations.sql
7. migrations/007_notifications_cms.sql
8. migrations/008_analytics.sql
9. migrations/009_policies_rls.sql
10. storage_policies.sql
11. realtime_enable.sql
12. seed_dev.sql (only for development/non-production)

How to run (Supabase SQL Editor):
- Open the SQL Editor in your Supabase project.
- Execute each script in the order above. All scripts are idempotent or guarded to reduce re-run errors.

How to run (psql helper script - recommended):
- Ensure .env has a valid DATABASE_URL for your Supabase Postgres (do not hardcode secrets in code).
- From the job_matching_backend directory:
  chmod +x scripts/run_migrations.sh
  ./scripts/run_migrations.sh
- To load development seed data as well:
  RUN_SEED=true ./scripts/run_migrations.sh

How to run (supabase CLI):
- Ensure you have the Supabase CLI installed and authenticated.
- You can concatenate and run per file order:
  supabase db execute --file docs/database/migrations/001_init.sql
  supabase db execute --file docs/database/migrations/002_profiles.sql
  ...
  supabase db execute --file docs/database/seed_dev.sql

Realtime Subscriptions (Frontend/Backend guidance):
- v_public_jobs maps to realtime on public.jobs (filter for is_published and not expired in client)
- v_user_notifications maps to realtime on public.notifications filtered by user_id = auth.uid()
- v_employer_applications maps to realtime on public.applications; join with jobs to filter employer_id
- v_events_outbox maps to realtime on public.analytics_events for event fanout

Storage Buckets:
- resumes (private): only owner and admins can read/write
- logos (public read): employers/admins can write
- attachments (private): only owner and admins can read/write

Vector/Embeddings:
- pgvector is enabled in 001_init.sql
- seekers_embeddings and jobs_embeddings store 768-d vectors
- match_jobs_for_seeker(user_id, k) helper provides top-k matches

RLS:
- Policies are centralized in 009_policies_rls.sql
- Admins (users.user_type='admin') have broad control as defined
- Employers can manage their jobs and related job_skills
- Job seekers can manage their own profiles, education, experience, skills, and applications

Notes:
- auth.users is managed by Supabase; this project uses a public.users table keyed by auth.users.id for application metadata.
- If you change embedding dimension, update 005_embeddings_match.sql and re-create indexes accordingly.
