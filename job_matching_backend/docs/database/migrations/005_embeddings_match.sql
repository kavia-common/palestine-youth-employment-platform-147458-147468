-- 005_embeddings_match.sql
-- Purpose: Create pgvector-backed embeddings tables for seekers and jobs + similarity search helpers

-- Embeddings dimension (adjust per model used across system)
do $$
begin
  if not exists (select 1 from pg_type where typname = 'vector') then
    raise exception 'pgvector extension not enabled; ensure 001_init.sql ran successfully';
  end if;
end$$;

-- Seekers embeddings
create table if not exists public.seekers_embeddings (
  user_id uuid primary key references public.job_seekers(user_id) on delete cascade,
  embedding vector(768) not null,
  updated_at timestamptz not null default now()
);
create index if not exists idx_seekers_embedding_ivfflat on public.seekers_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Jobs embeddings
create table if not exists public.jobs_embeddings (
  job_id uuid primary key references public.jobs(id) on delete cascade,
  embedding vector(768) not null,
  updated_at timestamptz not null default now()
);
create index if not exists idx_jobs_embedding_ivfflat on public.jobs_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);

alter table public.seekers_embeddings enable row level security;
alter table public.jobs_embeddings enable row level security;

-- Helper function: top-k jobs for a seeker by cosine distance
create or replace function public.match_jobs_for_seeker(p_user_id uuid, k int default 20)
returns table(job_id uuid, similarity float4)
language sql
stable
as $$
  select je.job_id, 1 - (se.embedding <=> je.embedding)::float4 as similarity
  from public.seekers_embeddings se
  join public.jobs_embeddings je on true
  where se.user_id = p_user_id
  order by se.embedding <-> je.embedding
  limit k
$$;

comment on function public.match_jobs_for_seeker is 'Returns top-k jobs for a seeker based on cosine similarity of embeddings.';
