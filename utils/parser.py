from __future__ import annotations
import re
import json
from pydantic import BaseModel, Field
from typing import Optional


class CandidateResult(BaseModel):
    candidate_name: str = ""
    email: str = "Not specified"
    summary: str = ""
    education: str = "Not specified"
    experience_years: float = 0.0
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)
    score: int = 0
    recommendation: str = "Interview"
    status: str = "Sourced"
    justification: str = ""
    technical_questions: list[str] = Field(default_factory=list)
    hr_questions: list[str] = Field(default_factory=list)
    notes: str = ""
    career_summary: str = ""
    technical_depth: list[str] = Field(default_factory=list)
    key_achievements: list[str] = Field(default_factory=list)
    career_trajectory: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    cultural_fit: str = ""
    growth_potential: str = ""


def _strip_fences(text: str) -> str:
    text = re.sub(r"```(?:json|JSON)?\s*\n?", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


def parse_json_from_llm(text: str) -> Optional[dict]:
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def _error_result(candidate_name: str, raw_output: str = "") -> CandidateResult:
    return CandidateResult(
        candidate_name=candidate_name,
        recommendation="Error - manual review needed",
        justification=f"Failed to parse structured output. Raw: {raw_output[:500]}",
    )


def build_candidate_result(
    candidate_name: str,
    summary_text: str,
    skill_match_text: str,
    score_text: str,
    hr_text: str,
    interview_text: str = "",
    deep_analysis_text: str = "",
    retry_fn=None,
) -> CandidateResult:
    raw_data = {
        "candidate_name": candidate_name,
        "summary": summary_text,
        "education": _extract_field(summary_text, "EDUCATION"),
        "experience_years": _extract_years(summary_text),
        "email": _extract_field(summary_text, "EMAIL"),
        "matching_skills": [],
        "missing_skills": [],
        "extra_skills": [],
        "score": 0,
        "recommendation": "Interview",
        "justification": "",
        "technical_questions": [],
        "hr_questions": [],
    }

    from ai.chains import (
        parse_score,
        parse_recommendation,
        parse_skill_lists,
        parse_interview_questions,
        parse_deep_analysis,
    )

    matching, missing, extra = parse_skill_lists(skill_match_text)
    raw_data["matching_skills"] = matching
    raw_data["missing_skills"] = missing
    raw_data["extra_skills"] = extra

    raw_data["score"] = parse_score(score_text)

    rec, justification = parse_recommendation(hr_text)
    raw_data["recommendation"] = rec
    raw_data["justification"] = justification

    if interview_text and rec.lower() in ("hire", "interview"):
        tech, beh = parse_interview_questions(interview_text)
        raw_data["technical_questions"] = tech
        raw_data["hr_questions"] = beh

    if deep_analysis_text:
        deep = parse_deep_analysis(deep_analysis_text)
        raw_data["career_summary"] = deep.get("career_summary", "")
        raw_data["technical_depth"] = deep.get("technical_depth", [])
        raw_data["key_achievements"] = deep.get("key_achievements", [])
        raw_data["career_trajectory"] = deep.get("career_trajectory", [])
        raw_data["strengths"] = deep.get("strengths", [])
        raw_data["weaknesses"] = deep.get("weaknesses", [])
        raw_data["cultural_fit"] = deep.get("cultural_fit", "")
        raw_data["growth_potential"] = deep.get("growth_potential", "")

    try:
        return CandidateResult(**raw_data)
    except Exception:
        return _error_result(candidate_name)


def _extract_field(text: str, label: str) -> str:
    pattern = rf"{label}:\s*(.+?)(?:\n|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "Not specified"


def _extract_years(text: str) -> float:
    patterns = [
        r"(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)",
        r"EXPERIENCE:\s*(\d+)",
        r"(\d+)\+?\s*years?",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return 0.0
