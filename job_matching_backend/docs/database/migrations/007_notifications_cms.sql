-- 007_notifications_cms.sql
-- Purpose: Views supporting realtime subscriptions and simplified reads

-- Public jobs view: only published and not expired
create or replace view public.v_public_jobs as
select
  j.id,
  j.title,
  j.description,
  j.location,
  j.employment_type,
  j.salary_min,
  j.salary_max,
  j.currency,
  j.is_remote,
  j.is_published,
  j.posted_at,
  j.expires_at,
  e.org_name as employer_name
from public.jobs j
join public.employers e on e.user_id = j.employer_id
where j.is_published = true and (j.expires_at is null or j.expires_at > now());

comment on view public.v_public_jobs is 'Publicly visible jobs used for frontend listing with realtime updates.';

-- User notifications view: personal notifications ordered by time
create or replace view public.v_user_notifications as
select
  n.id,
  n.user_id,
  n.type,
  n.title,
  n.body,
  n.read_at,
  n.created_at
from public.notifications n;

comment on view public.v_user_notifications is 'Per-user notifications feed. RLS on notifications applies.';

-- Employer applications view: employers see applications to their jobs
create or replace view public.v_employer_applications as
select
  a.id as application_id,
  a.job_id,
  a.seeker_id,
  a.status,
  a.created_at,
  a.updated_at,
  j.employer_id
from public.applications a
join public.jobs j on j.id = a.job_id;

comment on view public.v_employer_applications is 'Employer-facing applications feed by job. RLS on base tables applies.';

-- Events outbox for analytics/realtime fanout
create table if not exists public.analytics_events (
  id uuid primary key default uuid_generate_v4(),
  actor_id uuid,
  event_type text not null,
  payload jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_analytics_events_type_time on public.analytics_events(event_type, created_at desc);

alter table public.analytics_events enable row level security;

create or replace view public.v_events_outbox as
select id, actor_id, event_type, payload, created_at
from public.analytics_events;

comment on view public.v_events_outbox is 'Outbox view for analytics and websocket fanout.';
