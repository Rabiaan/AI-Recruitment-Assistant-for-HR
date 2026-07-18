import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in your .env file."
            )
        _client = create_client(url, key)
    return _client


def insert_job_description(title: str, raw_text: str) -> dict:
    client = get_client()
    result = (
        client.table("job_descriptions")
        .insert({"title": title, "raw_text": raw_text})
        .execute()
    )
    return result.data[0] if result.data else {}


def insert_candidate_result(
    jd_id: str,
    candidate_name: str,
    resume_text: str,
    summary: str = "",
    education: str = "",
    experience_years: float = 0.0,
    matching_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
    extra_skills: list[str] | None = None,
    score: int = 0,
    recommendation: str = "",
    justification: str = "",
    technical_questions: list[str] | None = None,
    hr_questions: list[str] | None = None,
) -> dict:
    client = get_client()
    row = {
        "jd_id": jd_id,
        "candidate_name": candidate_name,
        "resume_text": resume_text,
        "summary": summary,
        "education": education,
        "experience_years": experience_years,
        "matching_skills": matching_skills or [],
        "missing_skills": missing_skills or [],
        "extra_skills": extra_skills or [],
        "score": score,
        "recommendation": recommendation,
        "justification": justification,
        "technical_questions": technical_questions or [],
        "hr_questions": hr_questions or [],
    }
    result = client.table("candidates").insert(row).execute()
    return result.data[0] if result.data else {}


def fetch_history(limit: int = 20) -> list[dict]:
    client = get_client()
    result = (
        client.table("candidates")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def fetch_candidates_for_jd(jd_id: str) -> list[dict]:
    client = get_client()
    result = (
        client.table("candidates")
        .select("*")
        .eq("jd_id", jd_id)
        .order("score", desc=True)
        .execute()
    )
    return result.data or []


def fetch_jd_history(limit: int = 10) -> list[dict]:
    client = get_client()
    result = (
        client.table("job_descriptions")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []
