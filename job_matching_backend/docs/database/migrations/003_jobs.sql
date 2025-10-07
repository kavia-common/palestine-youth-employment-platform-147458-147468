-- 003_jobs.sql
-- Purpose: Create jobs, job_skills, applications, and preferences tables

create table if not exists public.jobs (
  id uuid primary key default uuid_generate_v4(),
  employer_id uuid not null references public.employers(user_id) on delete cascade,
  title text not null,
  description text,
  location text,
  employment_type text check (employment_type in ('full_time', 'part_time', 'contract', 'internship', 'temporary')),
  salary_min numeric,
  salary_max numeric,
  currency text,
  is_remote boolean default false,
  is_published boolean not null default false,
  posted_at timestamptz default now(),
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_jobs_employer on public.jobs(employer_id);
create index if not exists idx_jobs_title_trgm on public.jobs using gin (title gin_trgm_ops);
create index if not exists idx_jobs_location on public.jobs(location);

drop trigger if exists set_jobs_updated_at on public.jobs;
create trigger set_jobs_updated_at
before update on public.jobs
for each row execute function public.set_updated_at();

alter table public.jobs enable row level security;

create table if not exists public.job_skills (
  job_id uuid not null references public.jobs(id) on delete cascade,
  skill_id uuid not null references public.skills(id) on delete restrict,
  required boolean not null default true,
  weight numeric(4,2) default 1.0,
  primary key (job_id, skill_id)
);
create index if not exists idx_job_skills_skill on public.job_skills(skill_id);
alter table public.job_skills enable row level security;

create table if not exists public.applications (
  id uuid primary key default uuid_generate_v4(),
  job_id uuid not null references public.jobs(id) on delete cascade,
  seeker_id uuid not null references public.job_seekers(user_id) on delete cascade,
  cover_letter text,
  resume_url text,
  status text not null default 'submitted' check (status in ('submitted','review','interview','offer','rejected','withdrawn','hired')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists uniq_applications_job_seeker on public.applications(job_id, seeker_id);
create index if not exists idx_applications_job on public.applications(job_id);
create index if not exists idx_applications_seeker on public.applications(seeker_id);

drop trigger if exists set_applications_updated_at on public.applications;
create trigger set_applications_updated_at
before update on public.applications
for each row execute function public.set_updated_at();

alter table public.applications enable row level security;

-- Preferences per user
create table if not exists public.preferences (
  user_id uuid primary key references public.users(id) on delete cascade,
  notifications_enabled boolean not null default true,
  language text default 'en',
  theme text default 'system',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists set_preferences_updated_at on public.preferences;
create trigger set_preferences_updated_at
before update on public.preferences
for each row execute function public.set_updated_at();

alter table public.preferences enable row level security;
