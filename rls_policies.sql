-- Run this in Supabase Dashboard > SQL Editor

-- Enable RLS policies for anon (public) access
-- Adjust if you add auth later

alter table job_descriptions enable row level security;
alter table candidates enable row level security;

-- Allow anon insert/select on job_descriptions
create policy "Allow anon insert on job_descriptions"
  on job_descriptions for insert
  to anon
  with check (true);

create policy "Allow anon select on job_descriptions"
  on job_descriptions for select
  to anon
  using (true);

-- Allow anon insert/select on candidates
create policy "Allow anon insert on candidates"
  on candidates for insert
  to anon
  with check (true);

create policy "Allow anon select on candidates"
  on candidates for select
  to anon
  using (true);
