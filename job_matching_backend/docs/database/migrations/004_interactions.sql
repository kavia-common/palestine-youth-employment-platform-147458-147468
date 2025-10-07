-- 004_interactions.sql
-- Purpose: Notifications, CMS content, integrations, and audit logs

create table if not exists public.notifications (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(id) on delete cascade,
  type text not null,
  title text not null,
  body text,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists idx_notifications_user on public.notifications(user_id);
create index if not exists idx_notifications_unread on public.notifications(user_id) where read_at is null;

alter table public.notifications enable row level security;

-- CMS: news and FAQ
create table if not exists public.cms_news (
  id uuid primary key default uuid_generate_v4(),
  title text not null,
  body text not null,
  published boolean not null default false,
  published_at timestamptz,
  created_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists set_cms_news_updated_at on public.cms_news;
create trigger set_cms_news_updated_at
before update on public.cms_news
for each row execute function public.set_updated_at();

alter table public.cms_news enable row level security;

create table if not exists public.cms_faq (
  id uuid primary key default uuid_generate_v4(),
  question text not null,
  answer text not null,
  order_index int default 0,
  published boolean not null default true,
  created_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists set_cms_faq_updated_at on public.cms_faq;
create trigger set_cms_faq_updated_at
before update on public.cms_faq
for each row execute function public.set_updated_at();

alter table public.cms_faq enable row level security;

-- Integrations
create table if not exists public.integration_partners (
  id uuid primary key default uuid_generate_v4(),
  name text not null unique,
  base_url text,
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);
alter table public.integration_partners enable row level security;

create table if not exists public.integration_keys (
  id uuid primary key default uuid_generate_v4(),
  partner_id uuid not null references public.integration_partners(id) on delete cascade,
  key_name text not null,
  key_value text not null, -- store encrypted in Vault ideally
  created_at timestamptz not null default now(),
  unique (partner_id, key_name)
);
alter table public.integration_keys enable row level security;

create table if not exists public.integration_jobs_map (
  id uuid primary key default uuid_generate_v4(),
  partner_id uuid not null references public.integration_partners(id) on delete cascade,
  external_job_id text not null,
  internal_job_id uuid not null references public.jobs(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (partner_id, external_job_id)
);
create index if not exists idx_int_jobs_map_partner on public.integration_jobs_map(partner_id);
alter table public.integration_jobs_map enable row level security;

-- Audit logs
create table if not exists public.audit_logs (
  id bigserial primary key,
  actor_id uuid,
  action text not null,
  entity text not null,
  entity_id text not null,
  meta jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_audit_logs_entity on public.audit_logs(entity, entity_id);
alter table public.audit_logs enable row level security;
