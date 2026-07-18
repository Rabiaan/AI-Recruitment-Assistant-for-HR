import re
import time
from langchain_core.output_parsers import StrOutputParser
from .llm import get_llm
from utils.prompts import (
    summary_prompt,
    skill_match_prompt,
    score_prompt,
    hr_prompt,
    interview_questions_prompt,
)


def _invoke_with_retry(chain, inputs, max_retries=2, backoff=3.0):
    last_error = None
    for attempt in range(max_retries):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if any(kw in msg for kw in ("rate", "quota", "429", "503", "timeout")):
                if attempt < max_retries - 1:
                    time.sleep(backoff * (attempt + 1))
                    continue
            raise
    raise last_error


def build_summary_chain():
    llm = get_llm(temperature=0.2)
    return summary_prompt | llm | StrOutputParser()


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
