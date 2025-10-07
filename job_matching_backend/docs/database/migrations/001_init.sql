-- 001_init.sql
-- Purpose: Initialize extensions, helper schema, base auth mirror, and core users table scaffolding
-- Notes:
-- - Uses pgvector for semantic search
-- - Creates helper function for current auth role mapping when using Supabase
-- - Sets search_path and basic settings

-- Enable required extensions in the database (requires superuser in Supabase migration context)
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";
create extension if not exists "pg_trgm";
create extension if not exists "vector"; -- pgvector

-- Settings
set search_path = public, extensions;

-- Helper: in Supabase, auth.uid() is available. Provide a fallback for local psql if needed.
create or replace function public.current_user_id()
returns uuid
language sql
stable
as $$
  select coalesce(auth.uid(), null);
$$;

comment on function public.current_user_id is 'Returns the authenticated user id (uuid) when called via Supabase postgrest';

-- Base table: users (mirror metadata beyond auth.users)
-- Note: We do NOT recreate auth.users; instead keep a profile table keyed by id=auth.users.id
create table if not exists public.users (
  id uuid primary key,
  email text not null unique,
  user_type text not null check (user_type in ('job_seeker','employer','admin')),
  full_name text,
  phone text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_users_user_type on public.users(user_type);
create index if not exists idx_users_email_trgm on public.users using gin (email gin_trgm_ops);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end
$$;

drop trigger if exists set_users_updated_at on public.users;
create trigger set_users_updated_at
before update on public.users
for each row execute function public.set_updated_at();

-- RLS default off until dedicated policy migration (009) to keep order explicit
alter table public.users enable row level security;

-- Minimal RLS placeholders (locked down by default)
drop policy if exists "users_no_access" on public.users;
create policy "users_no_access" on public.users
  for all
  using (false)
  with check (false);

-- Vector base: define vectors for 768 dims (typical for MiniLM/all-MPNet)
-- We will create actual tables later in dedicated migration (005)
-- Just comment here for clarity.

-- Housekeeping comments
comment on table public.users is 'Application users profile table keyed by auth.users.id. user_type differentiates job seekers, employers, and admins.';
