-- 002_profiles.sql
-- Purpose: Create job seekers and employers domain profile tables and related entities

-- Job seekers profile
create table if not exists public.job_seekers (
  user_id uuid primary key references public.users(id) on delete cascade,
  bio text,
  location text,
  visibility boolean not null default true,
  desired_role text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_job_seekers_location on public.job_seekers(location);

drop trigger if exists set_job_seekers_updated_at on public.job_seekers;
create trigger set_job_seekers_updated_at
before update on public.job_seekers
for each row execute function public.set_updated_at();

alter table public.job_seekers enable row level security;

-- Employers profile
create table if not exists public.employers (
  user_id uuid primary key references public.users(id) on delete cascade,
  org_name text not null,
  website text,
  location text,
  verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_employers_org_name_trgm on public.employers using gin (org_name gin_trgm_ops);

drop trigger if exists set_employers_updated_at on public.employers;
create trigger set_employers_updated_at
before update on public.employers
for each row execute function public.set_updated_at();

alter table public.employers enable row level security;

-- Education and Experience tables for job seekers
create table if not exists public.education (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  institution text not null,
  degree text,
  field_of_study text,
  start_date date,
  end_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_education_user on public.education(user_id);

drop trigger if exists set_education_updated_at on public.education;
create trigger set_education_updated_at
before update on public.education
for each row execute function public.set_updated_at();

alter table public.education enable row level security;

create table if not exists public.experience (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null,
  company text,
  location text,
  start_date date,
  end_date date,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_experience_user on public.experience(user_id);

drop trigger if exists set_experience_updated_at on public.experience;
create trigger set_experience_updated_at
before update on public.experience
for each row execute function public.set_updated_at();

alter table public.experience enable row level security;

-- Skills catalog and seeker_skills
create table if not exists public.skills (
  id uuid primary key default uuid_generate_v4(),
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.seeker_skills (
  user_id uuid not null references public.users(id) on delete cascade,
  skill_id uuid not null references public.skills(id) on delete restrict,
  proficiency smallint check (proficiency between 1 and 5),
  years_experience numeric(4,1),
  created_at timestamptz not null default now(),
  primary key (user_id, skill_id)
);

create index if not exists idx_seeker_skills_skill on public.seeker_skills(skill_id);
create index if not exists idx_skills_name_trgm on public.skills using gin (name gin_trgm_ops);

alter table public.skills enable row level security;
alter table public.seeker_skills enable row level security;
