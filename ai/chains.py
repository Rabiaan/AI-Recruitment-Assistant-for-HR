from __future__ import annotations
import re
import time
from langchain_core.output_parsers import StrOutputParser
from .llm import get_llm
from utils.prompts import (
    summary_prompt,
    deep_analysis_prompt,
    skill_match_prompt,
    score_prompt,
    hr_prompt,
    interview_questions_prompt,
)

_token_usage_log: list[dict] = []


def get_token_usage_log() -> list[dict]:
    try:
        import streamlit as st
        return st.session_state.get("_token_log", _token_usage_log)
    except Exception:
        return _token_usage_log


def get_total_tokens_used() -> int:
    log = get_token_usage_log()
    return sum(entry.get("total_tokens", 0) for entry in log)


def _invoke_with_retry(chain, inputs, max_retries=5, backoff=60.0):
    last_error = None
    for attempt in range(max_retries):
        try:
            result = chain.invoke(inputs)
            try:
                meta = getattr(result, "usage_metadata", None)
                if meta:
                    entry = {
                        "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                        "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
                        "total_tokens": getattr(meta, "total_token_count", 0) or 0,
                        "model": getattr(chain, "model", "") if hasattr(chain, "model") else "",
                    }
                    _token_usage_log.append(entry)
                    try:
                        import streamlit as st
                        st.session_state.setdefault("_token_log", [])
                        st.session_state["_token_log"].append(entry)
                    except Exception:
                        pass
            except Exception:
                pass
            return result
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if any(kw in msg for kw in ("rate", "quota", "429", "503", "timeout", "resource_exhausted")):
                if attempt < max_retries - 1:
                    wait = backoff * (attempt + 1)
                    time.sleep(wait)
                    continue
            raise
    raise last_error


def build_summary_chain():
    llm = get_llm(temperature=0.2)
    return summary_prompt | llm | StrOutputParser()


def build_deep_analysis_chain():
    llm = get_llm(temperature=0.3)
    return deep_analysis_prompt | llm | StrOutputParser()


def build_skill_match_chain():
    llm = get_llm(temperature=0.2)
    return skill_match_prompt | llm | StrOutputParser()


def build_score_chain():
    llm = get_llm(temperature=0.2)
    return score_prompt | llm | StrOutputParser()


def build_hr_chain():
    llm = get_llm(temperature=0.2)
    return hr_prompt | llm | StrOutputParser()


def build_interview_questions_chain():
    llm = get_llm(temperature=0.3)
    return interview_questions_prompt | llm | StrOutputParser()


def parse_score(text: str) -> int:
    match = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        return max(0, min(100, val))
    numbers = re.findall(r"\b(\d{1,3})\b", text)
    for num in numbers:
        val = int(num)
        if 0 <= val <= 100:
            return val
    return 50


def parse_recommendation(text: str) -> tuple[str, str]:
    rec = "Interview"
    justification = text.strip()
    match = re.search(r"RECOMMENDATION:\s*(Hire|Interview|Reject)", text, re.IGNORECASE)
    if match:
        rec = match.group(1).capitalize()
    just_match = re.search(r"JUSTIFICATION:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    if just_match:
        justification = just_match.group(1).strip()
    return rec, justification


def parse_skill_lists(text: str) -> tuple[list[str], list[str], list[str]]:
    matching, missing, extra = [], [], []
    current = None
    for line in text.split("\n"):
        upper = line.strip().upper()
        if upper.startswith("MATCHING"):
            current = matching
        elif upper.startswith("MISSING"):
            current = missing
        elif upper.startswith("EXTRA"):
            current = extra
        elif current is not None and line.strip().startswith("-"):
            skill = line.strip().lstrip("-").strip()
            if skill:
                current.append(skill)
    return matching, missing, extra


def parse_interview_questions(text: str) -> tuple[list[str], list[str]]:
    technical, behavioral = [], []
    current = None
    for line in text.split("\n"):
        upper = line.strip().upper()
        if "TECHNICAL" in upper:
            current = technical
        elif "BEHAVIORAL" in upper or "HR" in upper:
            current = behavioral
        elif current is not None and line.strip().startswith("-"):
            q = line.strip().lstrip("-").strip()
            if q:
                current.append(q)
    return technical, behavioral


def parse_deep_analysis(text: str) -> dict:
    result = {
        "career_summary": "",
        "technical_depth": [],
        "key_achievements": [],
        "career_trajectory": [],
        "strengths": [],
        "weaknesses": [],
        "cultural_fit": "",
        "growth_potential": "",
    }
    current_section = None
    for line in text.split("\n"):
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("CAREER_SUMMARY:"):
            result["career_summary"] = stripped.split(":", 1)[1].strip()
            current_section = None
        elif "TECHNICAL_DEPTH" in upper:
            current_section = "technical_depth"
        elif "KEY_ACHIEVEMENTS" in upper:
            current_section = "key_achievements"
        elif "CAREER_TRAJECTORY" in upper:
            current_section = "career_trajectory"
        elif upper.startswith("STRENGTHS:"):
            current_section = "strengths"
        elif upper.startswith("WEAKNESSES:"):
            current_section = "weaknesses"
        elif "CULTURAL_FIT:" in upper:
            result["cultural_fit"] = stripped.split(":", 1)[1].strip()
            current_section = None
        elif "GROWTH_POTENTIAL:" in upper:
            result["growth_potential"] = stripped.split(":", 1)[1].strip()
            current_section = None
        elif current_section and stripped.startswith("-"):
            item = stripped.lstrip("-").strip()
            if item:
                result[current_section].append(item)
    return result
