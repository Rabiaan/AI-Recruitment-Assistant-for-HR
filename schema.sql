-- TalentAI HR Dashboard — Clean Schema
-- Run this in Supabase Dashboard > SQL Editor

DROP TABLE IF EXISTS candidate_activity CASCADE;
DROP TABLE IF EXISTS candidates CASCADE;
DROP TABLE IF EXISTS job_descriptions CASCADE;

CREATE TABLE job_descriptions (
  id uuid primary key default gen_random_uuid(),
  title text,
  raw_text text,
  created_at timestamptz default now()
);

CREATE TABLE candidates (
  id uuid primary key default gen_random_uuid(),
  jd_id uuid references job_descriptions(id) on delete cascade,
  candidate_name text,
  email text default '',
  resume_text text,
  summary text,
  education text,
  experience_years numeric,
  matching_skills text[],
  missing_skills text[],
  extra_skills text[],
  score int,
  recommendation text,
  status text default 'Sourced',
  justification text,
  technical_questions text[],
  hr_questions text[],
  notes text default '',
  career_summary text default '',
  technical_depth text[],
  key_achievements text[],
  career_trajectory text[],
  ai_strengths text[],
  ai_weaknesses text[],
  cultural_fit text default '',
  growth_potential text default '',
  created_at timestamptz default now()
);

CREATE TABLE candidate_activity (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references candidates(id) on delete cascade,
  activity_type text,
  description text,
  created_at timestamptz default now()
);

CREATE INDEX idx_candidates_jd ON candidates(jd_id);
CREATE INDEX idx_candidates_score ON candidates(score desc);
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_activity_candidate ON candidate_activity(candidate_id);

-- RLS
ALTER TABLE job_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_activity ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon all job_descriptions" ON job_descriptions FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon all candidates" ON candidates FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon all candidate_activity" ON candidate_activity FOR ALL TO anon USING (true) WITH CHECK (true);
