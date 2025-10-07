-- storage_policies.sql
-- Purpose: Create buckets and define storage policies for public/private access patterns

-- Create buckets (idempotent)
insert into storage.buckets (id, name, public)
values 
  ('resumes', 'resumes', false),
  ('logos', 'logos', true),
  ('attachments', 'attachments', false)
on conflict (id) do nothing;

-- resumes: private to owner and admins
create policy if not exists "resumes_owner_read" on storage.objects
  for select to authenticated
  using (bucket_id = 'resumes' and (owner = auth.uid() or exists(select 1 from public.users where id = auth.uid() and user_type='admin')));

create policy if not exists "resumes_owner_write" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'resumes' and owner = auth.uid());

create policy if not exists "resumes_owner_update" on storage.objects
  for update to authenticated
  using (bucket_id = 'resumes' and owner = auth.uid())
  with check (bucket_id = 'resumes' and owner = auth.uid());

-- logos: public read, admin/employer write
create policy if not exists "logos_public_read" on storage.objects
  for select using (bucket_id = 'logos');

create policy if not exists "logos_employer_write" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'logos' and exists(select 1 from public.users where id = auth.uid() and user_type in ('employer','admin')));

create policy if not exists "logos_employer_update" on storage.objects
  for update to authenticated
  using (bucket_id = 'logos' and exists(select 1 from public.users where id = auth.uid() and user_type in ('employer','admin')))
  with check (bucket_id = 'logos' and exists(select 1 from public.users where id = auth.uid() and user_type in ('employer','admin')));

-- attachments: private to owner and admins
create policy if not exists "attachments_owner_read" on storage.objects
  for select to authenticated
  using (bucket_id = 'attachments' and (owner = auth.uid() or exists(select 1 from public.users where id = auth.uid() and user_type='admin')));

create policy if not exists "attachments_owner_write" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'attachments' and owner = auth.uid());

create policy if not exists "attachments_owner_update" on storage.objects
  for update to authenticated
  using (bucket_id = 'attachments' and owner = auth.uid())
  with check (bucket_id = 'attachments' and owner = auth.uid());
