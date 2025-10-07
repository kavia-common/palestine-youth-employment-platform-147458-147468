-- 008_analytics.sql
-- Purpose: Additional analytics helpers and indexes

-- Example aggregate matview for jobs per location (could be refreshed periodically)
create materialized view if not exists public.mv_jobs_by_location as
select location, count(*) as jobs_count
from public.jobs
where is_published = true
group by location;

create index if not exists idx_mv_jobs_by_location on public.mv_jobs_by_location(location);
comment on materialized view public.mv_jobs_by_location is 'Aggregate of published jobs per location.';
