create table if not exists job_descriptions (
  id uuid primary key default gen_random_uuid(),
  title text,
  raw_text text,
  created_at timestamptz default now()
);

create table if not exists candidates (
  id uuid primary key default gen_random_uuid(),
  jd_id uuid references job_descriptions(id) on delete cascade,
  candidate_name text,
  resume_text text,
  summary text,
  education text,
  experience_years numeric,
  matching_skills text[],
  missing_skills text[],
  extra_skills text[],
  score int,
  recommendation text,
  justification text,
  technical_questions text[],
  hr_questions text[],
  created_at timestamptz default now()
);

create index if not exists candidates_jd_id on candidates(jd_id);
create index if not exists candidates_score on candidates(score desc);
