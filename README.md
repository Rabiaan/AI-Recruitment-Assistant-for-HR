# TalentAI — AI Recruitment Assistant Dashboard

An AI-powered recruitment dashboard that analyzes resumes against job descriptions using Google Gemini, assigns fit scores, ranks candidates, and generates tailored interview questions — all from a single Streamlit interface.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [AI Pipeline](#ai-pipeline)
- [Setup & Installation](#setup--installation)
- [Running Locally](#running-locally)
- [Sample Data](#sample-data)
- [Usage Walkthrough](#usage-walkthrough)
- [Limitations & Notes](#limitations--notes)

---

## How It Works

The application follows a multi-stage AI pipeline:

```
PDF Upload (JD + Resumes)
        |
        v
  pdfplumber extracts raw text from each PDF
        |
        v
  Six sequential Gemini LLM calls analyze each resume:
        |
        |--> 1. Summary Chain      --> Education, experience, email, highlights
        |--> 2. Deep Analysis      --> Career trajectory, strengths, weaknesses, cultural fit
        |--> 3. Skill Match Chain  --> Matching / missing / extra skills vs. JD
        |--> 4. Score Chain        --> 0-100 fit score with reasoning
        |--> 5. HR Chain           --> Hire / Interview / Reject recommendation
        |--> 6. Interview Chain    --> Tailored technical + behavioral questions
        |
        v
  Parsers extract structured data from LLM text output
        |
        v
  Pydantic CandidateResult model assembles all fields
        |
        v
  Dashboard renders: ranking table, candidate profiles, AI co-pilot chat
        |
        v
  Results persisted to Supabase (Postgres) for persistence across sessions
```

Each stage uses a dedicated **LangChain LCEL chain** (prompt template | LLM | output parser) with automatic retry logic and exponential backoff for rate-limited requests.

---

## Features

### Core AI Analysis
- **Resume Summarization** — Extracts education, experience, top skills, email, and key highlights
- **Deep Analysis** — Career summary, technical depth per skill, quantified achievements, career trajectory, strengths/weaknesses, cultural fit, and growth potential
- **Skill Matching** — Compares resume skills against JD requirements into matching, missing, and extra categories
- **Fit Scoring** — 0–100 score weighted by core skill match (50%), experience fit (30%), and bonus skills (20%)
- **Hire Recommendation** — Automated Hire / Interview / Reject decision with justification
- **Interview Questions** — Tailored technical and behavioral questions based on candidate profile and role

### Dashboard UI
- **Candidate Ranking** — Candidates sorted by AI match score with status filtering (Sourced / In Progress / Interview / Hired)
- **Candidate Profiles** — Full profile view with career trajectory timeline, skill tags, strengths/gaps cards, experience metrics
- **AI Co-Pilot Chat** — Ask follow-up questions about any candidate; powered by the full profile context
- **Search & Filter** — Search candidates by name, role, or skill; filter by pipeline stage
- **Stats Overview** — Real-time counts of candidates in each pipeline stage

### Persistence
- **Supabase Integration** — All analysis results stored in PostgreSQL via Supabase
- **Session Recovery** — Previous candidates loaded from DB on app restart
- **Activity Tracking** — Candidate activity log table for audit trail

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit (Python) |
| **AI / LLM** | LangChain + Google Gemini 2.0 Flash |
| **PDF Parsing** | pdfplumber |
| **Data Modeling** | Pydantic v2 |
| **Database** | Supabase (PostgreSQL) with Row Level Security |
| **Config** | python-dotenv |
| **Language** | Python 3.10+ |

---

## Project Structure

```
AI_Recruitment_Assistant/
├── app.py                      # Main Streamlit entry point (dashboard + upload UI)
│
├── ai/
│   ├── __init__.py
│   ├── chains.py               # LCEL chains: summary, deep analysis, skill match, score, HR, interview
│   ├── llm.py                  # Shared ChatGoogleGenerativeAI instance (Gemini 2.0 Flash)
│   └── db.py                   # Supabase client: insert, fetch, update operations
│
├── utils/
│   ├── __init__.py
│   ├── prompts.py              # ChatPromptTemplates for each analysis chain
│   ├── pdf_reader.py           # PDF text extraction via pdfplumber
│   ├── parser.py               # Pydantic CandidateResult model + LLM output parsers
│   └── icons.py                # Inline SVG icon helper (Lucide-style)
│
├── components/
│   ├── __init__.py
│   ├── ai_chat.py              # AI co-pilot chat panel component
│   ├── ranking.py              # Candidate ranking table and detail views
│   ├── sidebar.py              # Settings sidebar
│   └── uploader.py             # JD and resume upload UI
│
├── data/
│   ├── sample_jds/             # Sample job description PDFs
│   ├── sample_resumes/         # Sample resume PDFs
│   ├── AI_Engineer_JD.pdf
│   ├── Senior_Python_Developer_JD.pdf
│   ├── John_Doe.pdf
│   ├── Jane_Smith.pdf
│   ├── Alice_Johnson.pdf
│   ├── Bob_Williams.pdf
│   ├── Carol_Brown.pdf
│   ├── sample_jds.csv
│   └── sample_resumes.csv
│
├── outputs/                    # Generated analysis outputs
│
├── .env                        # Environment variables (not committed)
├── .env.example                # Template for .env
├── schema.sql                  # Supabase table definitions + indexes + RLS
├── rls_policies.sql            # Row Level Security policies
├── requirements.txt            # Python dependencies
├── runtime.txt                 # Python runtime version
├── .python-version             # Python version pin
└── README.md
```

---

## Database Schema

Three tables in Supabase (PostgreSQL):

### `job_descriptions`
| Column | Type | Description |
|---|---|---|
| `id` | uuid (PK) | Auto-generated UUID |
| `title` | text | JD title |
| `raw_text` | text | Full extracted JD text |
| `created_at` | timestamptz | Upload timestamp |

### `candidates`
| Column | Type | Description |
|---|---|---|
| `id` | uuid (PK) | Auto-generated UUID |
| `jd_id` | uuid (FK) | References `job_descriptions.id` |
| `candidate_name` | text | Candidate full name |
| `email` | text | Extracted email |
| `resume_text` | text | Full raw resume text |
| `summary` | text | AI-generated summary |
| `education` | text | Extracted education |
| `experience_years` | numeric | Years of experience |
| `matching_skills` | text[] | Skills matching the JD |
| `missing_skills` | text[] | Skills required but absent |
| `extra_skills` | text[] | Skills not in JD |
| `score` | int | AI fit score (0–100) |
| `recommendation` | text | Hire / Interview / Reject |
| `status` | text | Pipeline stage (default: Sourced) |
| `justification` | text | AI recommendation reasoning |
| `technical_questions` | text[] | Generated technical questions |
| `hr_questions` | text[] | Generated behavioral questions |
| `career_summary` | text | Professional overview |
| `technical_depth` | text[] | Skill proficiency levels |
| `key_achievements` | text[] | Quantified achievements |
| `career_trajectory` | text[] | Role history with impact |
| `ai_strengths` | text[] | Identified strengths |
| `ai_weaknesses` | text[] | Identified gaps |
| `cultural_fit` | text | Soft skills assessment |
| `growth_potential` | text | Trajectory assessment |

### `candidate_activity`
| Column | Type | Description |
|---|---|---|
| `id` | uuid (PK) | Auto-generated UUID |
| `candidate_id` | uuid (FK) | References `candidates.id` |
| `activity_type` | text | Type of activity |
| `description` | text | Activity details |

All tables have **Row Level Security** enabled with anon access policies.

---

## AI Pipeline

### Chain Architecture

Each analysis step is a LangChain LCEL chain:

```python
# Example: Skill Matching Chain
skill_match_prompt | llm | StrOutputParser()
#       ^                    ^         ^
# ChatPromptTemplate   Gemini 2.0   String output
```

### Six Sequential Chains

| # | Chain | Input | Output | Temperature |
|---|---|---|---|---|
| 1 | **Summary** | Resume text | Education, experience, skills, email, highlights | 0.2 |
| 2 | **Deep Analysis** | Resume text | Career summary, technical depth, achievements, trajectory, strengths/weaknesses, cultural fit, growth potential | 0.3 |
| 3 | **Skill Match** | JD text + Resume text | Matching / missing / extra skill lists | 0.2 |
| 4 | **Score** | JD text + Skill match | 0–100 integer score with reasoning | 0.2 |
| 5 | **HR Recommendation** | Score + Missing skills + Skill match | Hire / Interview / Reject + justification | 0.2 |
| 6 | **Interview Questions** | JD text + Resume summary | 3 technical + 3 behavioral questions | 0.3 |

### Parsing

LLM text output is parsed heuristically using regex-based parsers in `ai/chains.py`:

- `parse_score()` — Extracts integer from `SCORE: <n>` or falls back to first valid 0–100 number
- `parse_recommendation()` — Extracts `RECOMMENDATION: <Hire|Interview|Reject>` + justification
- `parse_skill_lists()` — Parses bulleted lists under MATCHING / MISSING / EXTRA headers
- `parse_interview_questions()` — Parses questions under TECHNICAL / BEHAVIORAL headers
- `parse_deep_analysis()` — Parses multi-section structured output into dict

All parsed data is assembled into a `CandidateResult` Pydantic model (`utils/parser.py`).

### Error Handling

- **Rate limiting**: Automatic retry with exponential backoff (15s, 30s, 45s) on 429/503/timeout errors
- **Quota exhaustion**: Graceful error message displayed to user instead of crash
- **Parse failures**: Candidates marked as "Review Needed" / "Error - manual review needed"
- **PDF failures**: Scanned/image-only PDFs detected and skipped with warning

---

## Setup & Installation

### Prerequisites

- **Python 3.10+**
- **Google Gemini API Key** — Get one at [ai.google.dev](https://ai.google.dev)
- **Supabase Project** (optional, for persistence) — Create at [supabase.com](https://supabase.com)

### 1. Clone & Create Virtual Environment

```bash
git clone <repo-url>
cd AI_Recruitment_Assistant

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
# Required — Google Gemini API key
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional — Override default model (defaults to gemini-2.0-flash)
GEMINI_MODEL=gemini-2.0-flash

# Required for persistence — Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 4. Set Up Database (Optional)

If using Supabase persistence:

1. Go to your Supabase project dashboard
2. Open **SQL Editor**
3. Run the contents of `schema.sql`

This creates the `job_descriptions`, `candidates`, and `candidate_activity` tables with RLS policies.

---

## Running Locally

```bash
streamlit run app.py
```

The dashboard opens at **http://localhost:8501**.

To run on a different port:

```bash
streamlit run app.py --server.port 8080
```

---

## Sample Data

The `data/` directory includes sample files for testing:

### Job Descriptions
| File | Role |
|---|---|
| `AI_Engineer_JD.pdf` | AI Engineer — ML models, NLP, computer vision, production deployment |
| `Senior_Python_Developer_JD.pdf` | Senior Python Developer — Backend services, APIs, database optimization |

### Resumes (mix of strong and weak matches)
| File | Background | Expected Fit |
|---|---|---|
| `John_Doe.pdf` | Senior Python Backend Engineer — 5+ years, FastAPI, PostgreSQL, AWS | Strong match for Python JD |
| `Jane_Smith.pdf` | Frontend Developer — 3 years, React, Node.js, TypeScript | Weak match for Python/AI JDs |
| `Alice_Johnson.pdf` | AI/ML Engineer — Deep learning, NLP, computer vision | Strong match for AI JD |
| `Bob_Williams.pdf` | DevOps Engineer — CI/CD, Docker, Kubernetes, cloud infra | Partial match |
| `Carol_Brown.pdf` | Junior Data Analyst — Python, SQL, basic ML | Weak match for senior roles |

---

## Usage Walkthrough

1. **Open the dashboard** at `http://localhost:8501`
2. **Navigate to Upload** using the nav bar
3. **Upload a Job Description** (PDF) — text is extracted and previewed
4. **Upload one or more Resumes** (PDF) — multiple files supported
5. **Click "Analyze N Candidates"** — watch the progress bar as each resume goes through the 6-chain AI pipeline
6. **View Results on the Dashboard**:
   - Left panel: Candidate list sorted by score with status filters
   - Center panel: Full candidate profile (skills, career timeline, strengths/gaps, AI justification)
   - Right panel: AI Co-Recruiter chat + Today's Interviews
7. **Ask Follow-up Questions** in the AI chat (e.g., "Recommend 5 technical interview questions for this candidate")
8. **Change Pipeline Stage** using the status dropdown on any candidate profile
9. **Search** candidates by name, role, or skill

---

## Limitations & Notes

- **PDF Text Only** — Scanned/image-based PDFs without extractable text are detected and skipped. OCR is not supported.
- **LLM Output Parsing** — Gemini responses are parsed heuristically. Unusual formatting may cause partial data loss (candidates appear as "Review Needed").
- **API Quota** — Gemini free tier has rate limits. Heavy usage may trigger 429 errors (automatic retry with backoff handles this).
- **Sequential Processing** — Resumes are analyzed one at a time (not parallelized) to respect API rate limits.
- **No Authentication** — Dashboard is open access. Supabase RLS is configured for anon access.
- **File Size Limit** — PDFs must be under 10 MB.
- **Model** — Defaults to `gemini-2.0-flash`. Override with `GEMINI_MODEL` env var for other Gemini models.
