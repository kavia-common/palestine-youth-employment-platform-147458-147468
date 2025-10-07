-- seed_dev.sql
-- Purpose: Seed minimal development data. Run only in non-production.

-- Create sample users
insert into public.users (id, email, user_type, full_name)
values
  ('00000000-0000-0000-0000-000000000001', 'alice.seeker@example.com', 'job_seeker', 'Alice Seeker'),
  ('00000000-0000-0000-0000-000000000002', 'bob.employer@example.com', 'employer', 'Bob Employer'),
  ('00000000-0000-0000-0000-000000000003', 'admin@example.com', 'admin', 'Admin User')
on conflict (id) do nothing;

-- Profiles
insert into public.job_seekers (user_id, bio, location, desired_role)
values ('00000000-0000-0000-0000-000000000001', 'Motivated graduate', 'Ramallah', 'Junior Developer')
on conflict (user_id) do nothing;

insert into public.employers (user_id, org_name, website, location, verified)
values ('00000000-0000-0000-0000-000000000002', 'TechCorp Palestine', 'https://techcorp.ps', 'Gaza', true)
on conflict (user_id) do nothing;

-- Skills
insert into public.skills (id, name) values
  (uuid_generate_v4(), 'Python'),
  (uuid_generate_v4(), 'SQL'),
  (uuid_generate_v4(), 'React')
on conflict do nothing;

-- A job
insert into public.jobs (id, employer_id, title, description, location, employment_type, salary_min, salary_max, currency, is_remote, is_published)
values (
  '10000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000002',
  'Junior Python Developer',
  'Work on backend APIs.',
  'Ramallah',
  'full_time',
  1200, 1800, 'USD', true, true
) on conflict (id) do nothing;

-- Application
insert into public.applications (job_id, seeker_id, cover_letter, status)
values ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'I am excited to apply!', 'submitted')
on conflict do nothing;

-- Preferences
insert into public.preferences (user_id, notifications_enabled, language)
values ('00000000-0000-0000-0000-000000000001', true, 'en')
on conflict (user_id) do nothing;

-- CMS
insert into public.cms_news (title, body, published, published_at, created_by)
values ('Welcome to YEP Jobs', 'We are live!', true, now(), '00000000-0000-0000-0000-000000000003')
on conflict do nothing;

insert into public.cms_faq (question, answer, order_index, published, created_by)
values ('How to apply?', 'Create a profile and submit applications.', 1, true, '00000000-0000-0000-0000-000000000003')
on conflict do nothing;

-- Notifications
insert into public.notifications (user_id, type, title, body)
values ('00000000-0000-0000-0000-000000000001', 'system', 'Welcome', 'Thanks for joining!')
on conflict do nothing;

-- Analytics event
insert into public.analytics_events (actor_id, event_type, payload)
values ('00000000-0000-0000-0000-000000000001', 'signup', '{"source":"dev_seed"}'::jsonb)
on conflict do nothing;
