# AI Recruitment Assistant Dashboard

An AI-powered recruitment dashboard built with Streamlit and LangChain that analyzes resumes against job descriptions, assigns fit scores, ranks candidates, and generates interview questions.

## Features

- **PDF Parsing**: Extracts text from JD and resume PDFs
- **AI Analysis**: Uses LangChain + Gemini 1.5 Flash to perform:
  - Resume summarization
  - Skill matching (matching / missing / extra)
  - 0–100 fit scoring
  - Hire/Interview/Reject recommendation
  - Tailored interview questions (technical + HR)
- **Candidate Ranking**: Sorts candidates by score with expandable detail cards
- **Export**: Download results as CSV

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
AI_Recruitment_Assistant/
├── ai/
│   ├── __init__.py
│   ├── chains.py          # LCEL chains for analysis steps
│   └── llm.py             # Shared ChatGoogleGenerativeAI instance
├── components/
│   ├── __init__.py
│   ├── ranking.py         # Candidate ranking table and detail views
│   ├── sidebar.py         # Settings sidebar
│   └── uploader.py        # JD and resume upload UI
├── data/
│   ├── sample_jds.csv
│   └── sample_resumes.csv
├── utils/
│   ├── __init__.py
│   ├── prompts.py         # ChatPromptTemplates for each chain
│   └── pdf_reader.py      # PDF text extraction
├── outputs/
├── app.py                 # Main Streamlit entry point
├── requirements.txt
└── README.md
```

## Usage

1. Enter your Google API Key in the sidebar (or set `GOOGLE_API_KEY` in `.env`).
2. Upload a Job Description (PDF).
3. Upload one or more Resumes (PDF).
4. Click **Analyze Resumes**.
5. View the ranking table, expand candidates for details, and download the CSV.

## Notes

- PDFs must contain extractable text. Scanned PDFs are skipped with a warning.
- The LLM outputs are parsed heuristically. If parsing fails, the candidate appears as "Review Needed".
- Output files are saved to the `outputs/` directory.

## Deliverables

- 5 sample resumes (mix of strong/weak matches)
- 2 sample JDs (different roles)
- Screenshots & 10-min demo video (to be recorded)
