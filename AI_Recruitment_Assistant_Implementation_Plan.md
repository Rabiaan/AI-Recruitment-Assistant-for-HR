# AI Recruitment Assistant Dashboard — Implementation Plan

A module-by-module build plan for the SMIT Batch 9 final project, mapped to a realistic dev sequence, tech choices, and a submission timeline.

---

## 1. Tech Stack Decisions

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit | Spec requires it; fastest way to get a working dashboard |
| LLM | Gemini 1.5 Flash (via `google-generativeai` / `langchain-google-genai`) | Free tier, fast, good enough for structured extraction |
| Orchestration | LangChain (`LCEL` chains, not legacy `LLMChain`) | Cleaner, matches Module 3 diagram (Prompt → LLM → Parser) |
| PDF parsing | `pypdf` (or `pdfplumber` if resumes have tables) | Lightweight, no system deps |
| Structured output | `PydanticOutputParser` or Gemini's native JSON mode | Reliability for Module 9 |
| Storage | CSV in `/data`, no DB for MVP | Matches "Future Implementations" — DB is a stretch goal |

---

## 2. Environment Setup (Day 0)

```bash
mkdir AI-Recruitment-Assistant && cd AI-Recruitment-Assistant
python -m venv venv && source venv/bin/activate
pip install streamlit langchain langchain-google-genai pypdf python-dotenv pandas
```

`.env`:
```
GOOGLE_API_KEY=your_key_here
```

Create the folder structure exactly as in the spec (`components/`, `utils/`, `ai/`, `data/`, `outputs/`) up front — it keeps Module 1–11 changes isolated to the right files and makes the demo video's "folder structure" section trivial to record.

---

## 3. Build Order (recommended, differs slightly from module numbering)

Building the AI pipeline before the UI is polished lets you test chains in isolation with `print()` instead of debugging Streamlit reruns at the same time.

### Step 1 — `utils/pdf_reader.py` (Module 2)
- `extract_text(uploaded_file) -> str` using `pypdf.PdfReader`
- Strip excessive whitespace/newlines (basic `re.sub(r'\n{2,}', '\n', text)`)
- Handle multi-page resumes and scanned/no-text PDFs gracefully (return empty string + warning, don't crash)
- **Display the extracted text** in the UI (spec's explicit Module 2 output) — e.g. an `st.expander("View Extracted Text")` per uploaded resume, so HR can sanity-check parsing worked before running the (paid) LLM calls

### Step 2 — `ai/llm.py` (Module 3 foundation)
- One shared `get_llm()` function returning a configured `ChatGoogleGenerativeAI` instance (temperature ~0.2 for consistency across candidates)
- Load API key from `.env` via `python-dotenv`

### Step 3 — `utils/prompts.py` + `ai/chains.py` (Modules 4–8)
Build each chain as `prompt | llm | parser` (LCEL). Suggested chain order and prompt goals:

1. **Resume Summary Chain** — extract education, years of experience, key skills as a short bulleted structure
2. **Skill Match Chain** — take resume text + JD text, output Matching / Missing / Extra skills lists
3. **Score Chain** — take the output of chain 2 (not raw text) and produce a single 0–100 score with weighting logic in the prompt (e.g., core requirements weigh more than nice-to-haves)
4. **HR Recommendation Chain** — take score + missing skills, output Hire/Interview/Reject + 2–3 line justification
5. **Interview Questions Chain** — only run for Hire/Interview candidates (skip for Reject to save API calls) — 3 technical + 3 HR questions tailored to resume + JD

**Chaining tip:** feed each chain's output into the next rather than re-sending raw resume text every time — cheaper, more consistent, and mirrors the architecture diagram's left-to-right dependency.

### Step 4 — Module 9: Structured Output
- Define a Pydantic model matching the target schema:
```python
class CandidateAnalysis(BaseModel):
    summary: str
    score: int
    matching_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]
    recommendation: str
    justification: str
    interview_questions: dict[str, list[str]]
```
- Use `PydanticOutputParser(pydantic_object=CandidateAnalysis)` and inject `parser.get_format_instructions()` into your final aggregating prompt, OR run each chain separately and assemble the dict yourself in Python (simpler, more debuggable — recommended for a course project since partial failures are easier to isolate per-chain).

### Step 5 — `components/sidebar.py` + `components/uploader.py` (Module 1)
- Sidebar: JD upload (single PDF) + resume upload (`st.file_uploader(..., accept_multiple_files=True)`)
- Main page: "Analyze Resumes" button, disabled until both JD and ≥1 resume are uploaded
- UI-only in this step — wire buttons to placeholder functions first, real logic later

### Step 6 — Wire UI to Pipeline (`app.py`)
- On button click: loop over resumes → extract text → run chain pipeline → collect results into a list of dicts
- Show a `st.spinner` per candidate or a progress bar (`st.progress`) since Gemini calls take a few seconds each
- Cache JD text extraction with `st.session_state` so it isn't re-parsed every rerun

### Step 7 — `components/ranking.py` (Module 10)
- Build a `pandas.DataFrame` from the results list
- Sort descending by score
- Color-code recommendation column (`st.dataframe` with `column_config` or a styled Streamlit table)
- Add expandable `st.expander` per candidate for full detail (summary, missing skills, questions, justification)
- **Candidate Comparison view** (explicit spec item, separate from the ranking table itself): let HR multi-select 2–3 candidates via `st.multiselect` and render a side-by-side `st.columns` layout — score, matching/missing skills, and recommendation lined up per candidate for direct comparison

### Step 8 — Module 11: Export
- `df.to_csv(index=False)` → `st.download_button`
- Save a timestamped copy to `/outputs` as well, per the folder structure

---

## 4. Suggested Weekly Timeline (assuming ~2–3 weeks to deadline)

| Week | Focus |
|---|---|
| Week 1 | Env setup, PDF reader, LLM connection, chains 1–3 tested standalone (no UI) |
| Week 2 | Chains 4–5, Pydantic schema, Streamlit UI wired to pipeline, ranking table |
| Week 3 | Polish (styling, error handling, sample data), README, screenshots, record + edit demo video, final GitHub push |

---

## 5. Error Handling / Edge Cases to Not Skip
- Empty/scanned PDF → show a friendly warning, skip that candidate rather than crashing the whole batch
- Gemini rate limits → wrap chain calls in try/except with a short retry/backoff, since you'll be calling it 5× per resume across multiple resumes
- Malformed JSON from LLM → `PydanticOutputParser` raises on failure; catch it and either retry once with a stricter prompt or fall back to a "manual review needed" row in the table
- JD or resume missing required sections → your prompts should explicitly tell the LLM to say "Not specified" rather than hallucinate

---

## 6. Sample Data & Deliverables Checklist
- [ ] GitHub repo initialized early (`git init`, push after each working module) — don't leave this to the end, it also gives you commit history to show progress
- [ ] Complete, working source code pushed
- [ ] README.md: setup steps, `.env` instructions, how to run (`streamlit run app.py`), project screenshots
- [ ] requirements.txt (`pip freeze > requirements.txt` once stable)
- [ ] 5 sample resumes (mix of strong/weak matches so the ranking table looks meaningful, not all 90+)
- [ ] 2 sample JDs (different roles, e.g. one dev role + one non-dev, to show generality)
- [ ] 10-minute demo video — script these sections in order, don't wing it:
  1. Project introduction
  2. Folder structure walkthrough
  3. Code explanation
  4. LangChain + LLM workflow
  5. Prompt templates
  6. Live demo — resume upload
  7. Live demo — job description input
  8. Live demo — resume summary
  9. Live demo — skill matching
  10. Live demo — candidate ranking
  11. Live demo — HR feedback
  12. Live demo — interview questions

---

## 7. Stretch Goals (all six from the spec, ordered by effort/impact)
1. **Radar chart comparison** — easiest visual win, use `plotly` inside Streamlit; one chain already gives you the sub-scores if you ask the LLM to rate Skills/Experience/Education/Projects/Communication separately
2. **Interactive candidate cards** — mostly a Streamlit layout change (`st.expander` → custom cards with `st.columns`), low new-logic cost
3. **Email draft generator** — one more LangChain prompt template (interview invite vs. rejection, branched on the recommendation field), reuses existing recommendation output
4. **Authentication** — simplest viable version is `streamlit-authenticator` with a hardcoded HR user list in a YAML config; skip building real user management for a course project
5. **Voice summary (TTS)** — feed the resume summary chain's output into `gTTS` or Google Cloud TTS, play back with `st.audio`; low effort once the summary chain exists
6. **Chat with resume (RAG)** — highest effort: needs a vector store (`FAISS` or `Chroma`) per resume, chunking + embeddings, and a retrieval chain; only attempt after core deliverables are done and video-recorded
7. **Database integration (SQLite/PostgreSQL)** — swap the CSV-in-`/data` approach for a `resumes` + `analyses` table; do this last since it touches almost every module (upload, pipeline, ranking) and is the highest-risk refactor this close to a deadline

---

Want me to scaffold the actual starting code (folder structure + `app.py` + one working chain) so you have something runnable to iterate from?
