-- 009_policies_rls.sql
-- Purpose: Define all RLS policies across schema for roles job_seeker, employer, admin

-- Helper predicates
create or replace function public.is_admin(u uuid)
returns boolean
language sql
stable
as $$
  select exists(select 1 from public.users where id = u and user_type = 'admin');
$$;

create or replace function public.is_employer(u uuid)
returns boolean
language sql
stable
as $$
  select exists(select 1 from public.users where id = u and user_type = 'employer');
$$;

create or replace function public.is_seeker(u uuid)
returns boolean
language sql
stable
as $$
  select exists(select 1 from public.users where id = u and user_type = 'job_seeker');
$$;

-- USERS
drop policy if exists "users_admin_full" on public.users;
create policy "users_admin_full" on public.users
  for all
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

drop policy if exists "users_self_read" on public.users;
create policy "users_self_read" on public.users
  for select
  using (id = auth.uid());

drop policy if exists "users_self_update" on public.users;
create policy "users_self_update" on public.users
  for update
  using (id = auth.uid())
  with check (id = auth.uid());

-- JOB_SEEKERS
drop policy if exists "job_seekers_admin_full" on public.job_seekers;
create policy "job_seekers_admin_full" on public.job_seekers
  for all
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

drop policy if exists "job_seekers_self_rw" on public.job_seekers;
create policy "job_seekers_self_rw" on public.job_seekers
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists "job_seekers_public_read" on public.job_seekers;
create policy "job_seekers_public_read" on public.job_seekers
  for select
  using (visibility = true);

-- EMPLOYERS
drop policy if exists "employers_admin_full" on public.employers;
create policy "employers_admin_full" on public.employers
  for all using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

drop policy if exists "employers_self_rw" on public.employers;
create policy "employers_self_rw" on public.employers
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- EDUCATION
drop policy if exists "education_owner_rw" on public.education;
create policy "education_owner_rw" on public.education
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists "education_admin_full" on public.education;
create policy "education_admin_full" on public.education
  for all using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

-- EXPERIENCE
drop policy if exists "experience_owner_rw" on public.experience;
create policy "experience_owner_rw" on public.experience
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists "experience_admin_full" on public.experience;
create policy "experience_admin_full" on public.experience
  for all using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

-- SKILLS
drop policy if exists "skills_read_all" on public.skills;
create policy "skills_read_all" on public.skills
  for select using (true);

drop policy if exists "skills_admin_write" on public.skills;
create policy "skills_admin_write" on public.skills
  for insert to authenticated, service_role using (is_admin(auth.uid())) with check (is_admin(auth.uid()));
create policy "skills_admin_update" on public.skills
  for update using (is_admin(auth.uid())) with check (is_admin(auth.uid()));
create policy "skills_admin_delete" on public.skills
  for delete using (is_admin(auth.uid()));

-- SEEKER_SKILLS
drop policy if exists "seeker_skills_owner_rw" on public.seeker_skills;
create policy "seeker_skills_owner_rw" on public.seeker_skills
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists "seeker_skills_admin_full" on public.seeker_skills;
create policy "seeker_skills_admin_full" on public.seeker_skills
  for all using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

-- JOBS
drop policy if exists "jobs_public_select" on public.jobs;
create policy "jobs_public_select" on public.jobs
  for select using (is_published = true);

drop policy if exists "jobs_employer_rw" on public.jobs;
create policy "jobs_employer_rw" on public.jobs
  using (employer_id = auth.uid() or is_admin(auth.uid()))
  with check (employer_id = auth.uid() or is_admin(auth.uid()));

-- JOB_SKILLS
drop policy if exists "job_skills_owner_rw" on public.job_skills;
create policy "job_skills_owner_rw" on public.job_skills
  using (exists (select 1 from public.jobs j where j.id = job_id and (j.employer_id = auth.uid() or is_admin(auth.uid()))))
  with check (exists (select 1 from public.jobs j where j.id = job_id and (j.employer_id = auth.uid() or is_admin(auth.uid()))));

-- APPLICATIONS
drop policy if exists "applications_view_for_involved" on public.applications;
create policy "applications_view_for_involved" on public.applications
  for select using (
    seeker_id = auth.uid()
    or exists (select 1 from public.jobs j where j.id = job_id and (j.employer_id = auth.uid() or is_admin(auth.uid())))
  );

drop policy if exists "applications_seeker_create" on public.applications;
create policy "applications_seeker_create" on public.applications
  for insert with check (seeker_id = auth.uid());

drop policy if exists "applications_seeker_update_own" on public.applications;
create policy "applications_seeker_update_own" on public.applications
  for update using (seeker_id = auth.uid()) with check (seeker_id = auth.uid());

drop policy if exists "applications_employer_update_status" on public.applications;
create policy "applications_employer_update_status" on public.applications
  for update using (exists (select 1 from public.jobs j where j.id = job_id and (j.employer_id = auth.uid() or is_admin(auth.uid()))))
  with check (true);

-- PREFERENCES
drop policy if exists "preferences_owner_rw" on public.preferences;
create policy "preferences_owner_rw" on public.preferences
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- NOTIFICATIONS
drop policy if exists "notifications_owner_rw" on public.notifications;
create policy "notifications_owner_rw" on public.notifications
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- CMS
drop policy if exists "cms_news_public_read" on public.cms_news;
create policy "cms_news_public_read" on public.cms_news
  for select using (published = true);

drop policy if exists "cms_news_admin_rw" on public.cms_news;
create policy "cms_news_admin_rw" on public.cms_news
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

drop policy if exists "cms_faq_public_read" on public.cms_faq;
create policy "cms_faq_public_read" on public.cms_faq
  for select using (published = true);

drop policy if exists "cms_faq_admin_rw" on public.cms_faq;
create policy "cms_faq_admin_rw" on public.cms_faq
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

-- INTEGRATIONS
drop policy if exists "integration_partners_admin_rw" on public.integration_partners;
create policy "integration_partners_admin_rw" on public.integration_partners
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

drop policy if exists "integration_keys_admin_rw" on public.integration_keys;
create policy "integration_keys_admin_rw" on public.integration_keys
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

drop policy if exists "integration_jobs_map_admin_rw" on public.integration_jobs_map;
create policy "integration_jobs_map_admin_rw" on public.integration_jobs_map
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

-- AUDIT LOGS
drop policy if exists "audit_logs_admin_read" on public.audit_logs;
create policy "audit_logs_admin_read" on public.audit_logs
  for select using (is_admin(auth.uid()));

-- ANALYTICS EVENTS
drop policy if exists "analytics_events_admin_rw" on public.analytics_events;
create policy "analytics_events_admin_rw" on public.analytics_events
  using (is_admin(auth.uid()))
  with check (is_admin(auth.uid()));

-- EMBEDDINGS
drop policy if exists "seekers_embeddings_owner_rw" on public.seekers_embeddings;
create policy "seekers_embeddings_owner_rw" on public.seekers_embeddings
  using (user_id = auth.uid() or is_admin(auth.uid()))
  with check (user_id = auth.uid() or is_admin(auth.uid()));

drop policy if exists "jobs_embeddings_employer_admin_rw" on public.jobs_embeddings;
create policy "jobs_embeddings_employer_admin_rw" on public.jobs_embeddings
  using (exists (select 1 from public.jobs j where j.id = jobs_embeddings.job_id and (j.employer_id = auth.uid() or is_admin(auth.uid()))))
  with check (exists (select 1 from public.jobs j where j.id = jobs_embeddings.job_id and (j.employer_id = auth.uid() or is_admin(auth.uid()))));
