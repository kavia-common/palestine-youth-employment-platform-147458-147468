-- realtime_enable.sql
-- Purpose: Enable Supabase Realtime replication for selected tables and views

-- Tables with realtime replication
-- Supabase Realtime listens to the 'realtime' publication; add needed relations.
alter publication supabase_realtime add table
  public.jobs,
  public.applications,
  public.notifications,
  public.cms_news,
  public.cms_faq,
  public.analytics_events;

-- Views for realtime (logical replication of views requires triggers via supabase) - use supabase_realtime on base tables,
-- clients should subscribe to changes on views if supported, otherwise on base tables. We still add comment guidance.
comment on view public.v_public_jobs is 'Subscribe: supabase.channel("realtime:public:jobs") with filters (is_published = true, expires_at > now())';
comment on view public.v_user_notifications is 'Subscribe: supabase.channel("realtime:public:notifications") filtered by user_id = auth.uid()';
comment on view public.v_employer_applications is 'Subscribe: supabase.channel("realtime:public:applications") and join jobs to filter employer_id';
comment on view public.v_events_outbox is 'Subscribe: supabase.channel("realtime:public:analytics_events") for event fanout';

-- Ensure RLS is enabled already (handled in previous migrations).
