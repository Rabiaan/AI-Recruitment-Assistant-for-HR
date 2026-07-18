from __future__ import annotations
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from components.uploader import render_uploader
from components.ranking import render_candidate_list, render_candidate_profile
from components.ai_chat import render_ai_chat
from ai.chains import (
    build_summary_chain,
    build_skill_match_chain,
    build_score_chain,
    build_hr_chain,
    build_interview_questions_chain,
    parse_score,
    parse_recommendation,
    parse_skill_lists,
    parse_interview_questions,
    _invoke_with_retry,
)
from utils.parser import CandidateResult, build_candidate_result

NOT_FOUND = "Not Found"

SYSTEM_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"


def inject_global_css():
    st.markdown(f"""
    <style>
    :root {{
        --slate-950: #020617; --slate-900: #0f172a; --slate-850: #131c2e;
        --slate-800: #1e293b; --slate-700: #334155; --slate-600: #475569;
        --slate-500: #64748b; --slate-400: #94a3b8; --slate-300: #cbd5e1;
        --slate-200: #e2e8f0; --slate-100: #f1f5f9; --slate-50: #f8fafc;
        --indigo-700: #4338ca; --indigo-600: #4f46e5; --indigo-500: #6366f1;
        --indigo-400: #818cf8; --indigo-300: #a5b4fc; --indigo-200: #c7d2fe;
        --indigo-100: #e0e7ff; --indigo-50: #eef2ff;
        --blue-600: #2563eb; --blue-500: #3b82f6; --blue-100: #dbeafe;
        --blue-50: #eff6ff;
        --purple-600: #9333ea; --purple-100: #f3e8ff; --purple-50: #faf5ff;
        --amber-600: #d97706; --amber-500: #f59e0b; --amber-100: #fef3c7;
        --amber-50: #fffbeb;
        --emerald-600: #059669; --emerald-500: #10b981; --emerald-100: #d1fae5;
        --emerald-50: #ecfdf5;
        --red-600: #dc2626; --red-100: #fee2e2; --red-50: #fef2f2;
        --green-600: #16a34a; --green-500: #22c55e;
    }}

    .stApp {{
        font-family: {SYSTEM_FONT};
        background: var(--slate-50);
        color: var(--slate-900);
    }}
    .stApp header[data-testid="stHeader"] {{ background: transparent; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}

    /* ===== GLOBAL HEADER ===== */
    .talent-header {{
        background: var(--slate-900);
        border-bottom: 1px solid var(--slate-700);
        padding: 0 24px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 999;
        margin: -1rem -1rem 0 -1rem;
    }}
    .talent-logo {{
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 220px;
    }}
    .talent-logo-icon {{
        width: 32px; height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, var(--indigo-500), var(--indigo-700));
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 15px;
        box-shadow: 0 2px 8px rgba(99,102,241,0.3);
    }}
    .talent-logo-text h1 {{
        font-size: 15px; font-weight: 700; color: #ffffff;
        margin: 0; display: flex; align-items: center; gap: 8px;
    }}
    .talent-badge {{
        font-size: 9px; font-weight: 600; padding: 2px 7px;
        border-radius: 9999px; background: var(--indigo-500);
        color: white; letter-spacing: 0.5px;
    }}

    /* Search bar */
    .talent-search {{
        flex: 1;
        max-width: 480px;
        margin: 0 24px;
        position: relative;
    }}
    .talent-search input {{
        width: 100%;
        background: var(--slate-800);
        border: 1px solid var(--slate-700);
        border-radius: 8px;
        padding: 8px 12px 8px 36px;
        color: var(--slate-300);
        font-size: 13px;
        font-family: {SYSTEM_FONT};
        outline: none;
        transition: border-color 0.15s;
    }}
    .talent-search input:focus {{ border-color: var(--indigo-500); }}
    .talent-search input::placeholder {{ color: var(--slate-500); }}
    .talent-search-icon {{
        position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
        color: var(--slate-500); font-size: 13px;
    }}

    /* User info */
    .talent-user {{
        display: flex; align-items: center; gap: 10px;
        min-width: 200px; justify-content: flex-end;
    }}
    .talent-user-info {{ text-align: right; }}
    .talent-user-email {{ font-size: 11px; font-weight: 600; color: var(--slate-300); }}
    .talent-user-role {{
        font-size: 9px; color: var(--indigo-400);
        font-family: {MONO_FONT}; letter-spacing: 1px; text-transform: uppercase;
    }}
    .talent-avatar {{
        width: 32px; height: 32px; border-radius: 50%;
        background: var(--indigo-600);
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 700; font-size: 11px;
    }}

    /* ===== STATS BANNER ===== */
    .stats-banner {{
        background: var(--slate-900);
        padding: 12px 24px 16px;
        border-bottom: 1px solid var(--slate-700);
        margin: 0 -1rem;
    }}
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        max-width: 1400px;
        margin: 0 auto;
    }}
    .stat-card {{
        padding: 14px 16px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        border: 1px solid transparent;
        transition: transform 0.15s, box-shadow 0.15s;
    }}
    .stat-card:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
    .stat-icon {{
        width: 40px; height: 40px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; flex-shrink: 0;
    }}
    .stat-label {{ font-size: 11px; color: var(--slate-400); font-weight: 500; }}
    .stat-value {{ font-size: 22px; font-weight: 800; color: white; line-height: 1.2; }}

    .stat-blue {{ background: rgba(37,99,235,0.08); border-color: rgba(37,99,235,0.15); }}
    .stat-blue .stat-icon {{ background: rgba(37,99,235,0.15); color: var(--blue-500); }}
    .stat-purple {{ background: rgba(147,51,234,0.08); border-color: rgba(147,51,234,0.15); }}
    .stat-purple .stat-icon {{ background: rgba(147,51,234,0.15); color: var(--purple-600); }}
    .stat-amber {{ background: rgba(217,119,6,0.08); border-color: rgba(217,119,6,0.15); }}
    .stat-amber .stat-icon {{ background: rgba(217,119,6,0.15); color: var(--amber-500); }}
    .stat-emerald {{ background: rgba(5,150,105,0.08); border-color: rgba(5,150,105,0.15); }}
    .stat-emerald .stat-icon {{ background: rgba(5,150,105,0.15); color: var(--emerald-500); }}

    /* ===== SECTION LABELS ===== */
    .section-label {{
        font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px;
        color: var(--slate-400); font-family: {MONO_FONT}; font-weight: 600;
    }}

    /* ===== CANDIDATE CARDS ===== */
    .candidate-card {{
        padding: 12px 14px;
        border-radius: 10px;
        border: 1px solid var(--slate-200);
        cursor: pointer;
        transition: all 0.15s;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 6px;
        background: white;
    }}
    .candidate-card:hover {{ background: var(--slate-50); border-color: var(--slate-300); }}
    .candidate-card.selected {{
        background: var(--indigo-50);
        border-color: var(--indigo-300);
        box-shadow: 0 0 0 1px var(--indigo-200);
    }}

    .initials-badge {{
        width: 40px; height: 40px; min-width: 40px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 13px;
        color: white;
    }}
    .candidate-name {{ font-weight: 600; font-size: 13px; color: var(--slate-900); }}
    .candidate-title {{ font-size: 11px; color: var(--slate-500); margin-top: 2px; }}
    .candidate-date {{ font-size: 10px; color: var(--slate-400); margin-top: 4px; font-family: {MONO_FONT}; }}

    .score-pill {{
        font-size: 10px; font-weight: 700; padding: 3px 8px;
        border-radius: 6px; font-family: {MONO_FONT};
    }}
    .score-high {{ background: var(--emerald-100); color: var(--emerald-600); }}
    .score-mid {{ background: var(--amber-100); color: var(--amber-600); }}
    .score-low {{ background: var(--red-100); color: var(--red-600); }}

    .pipeline-pill {{
        font-size: 9px; font-weight: 600; padding: 2px 8px;
        border-radius: 9999px; border: 1px solid; letter-spacing: 0.3px;
        display: inline-block; margin-top: 6px;
    }}
    .pill-sourced {{ background: var(--slate-100); color: var(--slate-600); border-color: var(--slate-200); }}
    .pill-in-progress {{ background: var(--purple-50); color: var(--purple-600); border-color: #e9d5ff; }}
    .pill-interview {{ background: var(--amber-50); color: var(--amber-600); border-color: #fde68a; }}
    .pill-hired {{ background: var(--emerald-50); color: var(--emerald-600); border-color: #a7f3d0; }}

    /* ===== PIPELINE TABS ===== */
    .pipeline-tabs {{
        display: flex; background: var(--slate-100);
        border-radius: 10px; padding: 3px; gap: 3px; margin-bottom: 12px;
    }}
    .pipeline-tab {{
        flex: 1; text-align: center; padding: 7px 4px;
        border-radius: 8px; font-size: 11px; font-weight: 500;
        cursor: pointer; border: none; background: transparent;
        color: var(--slate-500); transition: all 0.15s;
    }}
    .pipeline-tab.active {{
        background: white; color: var(--slate-900);
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}

    /* ===== PROFILE ===== */
    .profile-header {{
        padding: 20px; border-bottom: 1px solid var(--slate-100);
        display: flex; align-items: center; justify-content: space-between;
    }}
    .profile-avatar-lg {{
        width: 48px; height: 48px; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 16px; color: white;
    }}
    .metric-card {{
        padding: 14px; background: var(--slate-50);
        border-radius: 10px; border: 1px solid var(--slate-200);
        text-align: center;
    }}
    .metric-label {{
        font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px;
        color: var(--slate-400); font-family: {MONO_FONT}; font-weight: 600;
    }}
    .metric-value {{ font-size: 18px; font-weight: 800; color: var(--slate-900); margin-top: 4px; }}

    /* ===== SKILL TAGS ===== */
    .skill-tag {{
        display: inline-block; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-weight: 500;
        margin: 3px; border: 1px solid transparent;
    }}
    .tag-match {{ background: var(--emerald-50); color: var(--emerald-600); border-color: #a7f3d0; }}
    .tag-miss {{ background: var(--red-50); color: var(--red-600); border-color: #fecaca; }}
    .tag-extra {{ background: var(--blue-50); color: var(--blue-600); border-color: #bfdbfe; }}

    /* ===== STRENGTHS / GAPS ===== */
    .strengths-card {{
        background: var(--emerald-50); border: 1px solid #a7f3d0;
        border-radius: 10px; padding: 14px;
    }}
    .gaps-card {{
        background: var(--red-50); border: 1px solid #fecaca;
        border-radius: 10px; padding: 14px;
    }}
    .card-title {{
        font-size: 11px; font-weight: 600; display: flex;
        align-items: center; gap: 6px; margin-bottom: 8px;
    }}

    /* ===== TIMELINE ===== */
    .tl-item {{ position: relative; padding-left: 28px; margin-bottom: 20px; }}
    .tl-dot {{
        position: absolute; left: 6px; top: 5px;
        width: 10px; height: 10px; border-radius: 50%;
        border: 2px solid var(--indigo-500); background: white;
    }}
    .tl-line {{
        position: absolute; left: 10px; top: 20px;
        bottom: -12px; width: 1px; background: var(--slate-200);
    }}
    .tl-meta {{
        font-size: 10px; color: var(--slate-400);
        font-family: {MONO_FONT};
        display: flex; justify-content: space-between;
    }}
    .tl-role {{ font-size: 13px; font-weight: 700; color: var(--slate-900); margin-top: 2px; }}
    .tl-desc {{ font-size: 11px; color: var(--slate-600); margin-top: 4px; line-height: 1.5; }}

    /* ===== PROGRESS BAR ===== */
    .pref-bar-bg {{
        width: 100%; height: 10px; border-radius: 9999px;
        background: var(--slate-100); overflow: hidden;
        display: flex; margin-top: 6px;
    }}
    .pref-bar-fill {{ height: 100%; transition: width 0.3s; }}
    .pref-legend {{ display: flex; gap: 14px; margin-top: 8px; flex-wrap: wrap; }}
    .pref-legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--slate-600); }}
    .pref-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}

    /* ===== RADIAL GAUGE ===== */
    .gauge-container {{ text-align: center; }}
    .gauge-label {{ font-size: 10px; color: var(--slate-500); margin-top: 4px; font-family: {MONO_FONT}; }}

    /* ===== AI CHAT ===== */
    .ai-panel {{
        background: var(--slate-900); color: var(--slate-300);
        border-radius: 14px; padding: 16px; border: 1px solid var(--slate-700);
    }}
    .ai-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 12px; border-bottom: 1px solid var(--slate-800);
        margin-bottom: 12px;
    }}
    .ai-msg-user {{
        background: var(--indigo-600); color: white;
        border-radius: 12px 12px 4px 12px;
        padding: 10px 12px; max-width: 90%; font-size: 12px;
    }}
    .ai-msg-ai {{
        background: var(--slate-800); color: var(--slate-300);
        border-radius: 12px 12px 12px 4px;
        padding: 10px 12px; max-width: 90%; font-size: 12px;
        border: 1px solid var(--slate-700);
    }}
    .ai-preset {{
        background: var(--slate-800); border: 1px solid var(--slate-700);
        border-radius: 8px; padding: 8px 10px; font-size: 10px;
        color: var(--slate-300); cursor: pointer; width: 100%;
        margin-bottom: 4px; text-align: left; transition: background 0.15s;
    }}
    .ai-preset:hover {{ background: var(--slate-700); }}

    /* ===== SCHEDULE CARD ===== */
    .schedule-card {{
        background: white; border: 1px solid var(--slate-200);
        border-radius: 12px; padding: 14px; margin-bottom: 8px;
    }}
    .schedule-time {{
        font-size: 11px; font-weight: 700; color: var(--indigo-600);
        font-family: {MONO_FONT};
    }}
    .schedule-title {{ font-size: 12px; font-weight: 600; color: var(--slate-900); margin-top: 4px; }}
    .schedule-meta {{ font-size: 10px; color: var(--slate-500); margin-top: 2px; }}
    .schedule-type {{
        font-size: 9px; font-weight: 600; padding: 2px 6px;
        border-radius: 4px; display: inline-block; margin-top: 6px;
    }}
    .type-interview {{ background: var(--amber-100); color: var(--amber-600); }}
    .type-1on1 {{ background: var(--blue-100); color: var(--blue-600); }}

    /* ===== FOOTER ===== */
    .talent-footer {{
        background: var(--slate-950); color: var(--slate-600);
        padding: 20px 24px; border-top: 1px solid var(--slate-800);
        font-size: 10px; font-family: {MONO_FONT};
        margin: 2rem -1rem -1rem -1rem;
    }}

    /* ===== EMPTY STATE ===== */
    .empty-state {{ text-align: center; padding: 40px; color: var(--slate-400); }}

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {{ background: var(--slate-50); }}
    [data-testid="stSidebar"] .stMarkdown h3 {{ color: var(--indigo-600); }}

    /* ===== ANIMATIONS ===== */
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
    .pulse-dot {{
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--green-500);
        animation: pulse 2s infinite; display: inline-block;
    }}

    /* ===== COLUMN PADDING ===== */
    .col-left {{ padding-right: 8px; }}
    .col-mid {{ padding: 0 8px; }}
    .col-right {{ padding-left: 8px; }}
    </style>
    """, unsafe_allow_html=True)


def analyze_resume(resume_name: str, resume_text: str, jd_text: str) -> CandidateResult:
    try:
        summary = _invoke_with_retry(build_summary_chain(), {"resume_text": resume_text})
        skill_match = _invoke_with_retry(build_skill_match_chain(), {"jd_text": jd_text, "resume_text": resume_text})
        score_text = _invoke_with_retry(build_score_chain(), {"jd_text": jd_text, "skill_match": skill_match})
        _, missing, _ = parse_skill_lists(skill_match)
        score = parse_score(score_text)
        hr_text = _invoke_with_retry(build_hr_chain(), {"score": str(score), "missing_skills": ", ".join(missing), "skill_match": skill_match})
        interview_text = ""
        rec, _ = parse_recommendation(hr_text)
        if rec.lower() in ("hire", "interview"):
            interview_text = _invoke_with_retry(build_interview_questions_chain(), {"jd_text": jd_text, "summary": summary})
        return build_candidate_result(candidate_name=resume_name, summary_text=summary, skill_match_text=skill_match, score_text=score_text, hr_text=hr_text, interview_text=interview_text)
    except Exception as e:
        return CandidateResult(candidate_name=resume_name, recommendation="Error - manual review needed", justification=f"Analysis failed: {e}")


def persist_to_supabase(jd_id: str, results: list[CandidateResult], resume_texts: dict[str, str]):
    try:
        from ai.db import insert_candidate_result
        for r in results:
            insert_candidate_result(
                jd_id=jd_id, candidate_name=r.candidate_name, resume_text=resume_texts.get(r.candidate_name, ""),
                summary=r.summary, education=r.education, experience_years=r.experience_years,
                matching_skills=r.matching_skills, missing_skills=r.missing_skills, extra_skills=r.extra_skills,
                score=r.score, recommendation=r.recommendation, justification=r.justification,
                technical_questions=r.technical_questions, hr_questions=r.hr_questions, status=r.status,
            )
        return True
    except Exception:
        return False


def export_csv(results: list[CandidateResult]) -> tuple[bytes, str]:
    rows = []
    for r in results:
        rows.append({
            "Name": r.candidate_name, "Score": r.score, "Recommendation": r.recommendation,
            "Status": r.status, "Summary": r.summary, "Education": r.education,
            "Experience (yrs)": r.experience_years, "Matching Skills": "; ".join(r.matching_skills),
            "Missing Skills": "; ".join(r.missing_skills), "Extra Skills": "; ".join(r.extra_skills),
            "Justification": r.justification, "Technical Questions": " | ".join(r.technical_questions),
            "HR Questions": " | ".join(r.hr_questions),
        })
    df = pd.DataFrame(rows).sort_values("Score", ascending=False)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    filename = f"candidate_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    os.makedirs("outputs", exist_ok=True)
    with open(os.path.join("outputs", filename), "wb") as f:
        f.write(csv_bytes)
    return csv_bytes, filename


BADGE_COLORS = [
    "#4f46e5", "#7c3aed", "#2563eb", "#0891b2", "#059669",
    "#d97706", "#dc2626", "#c026d3", "#0d9488", "#6366f1",
]


def get_badge_color(name: str) -> str:
    h = sum(ord(c) for c in name)
    return BADGE_COLORS[h % len(BADGE_COLORS)]


def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if name else "?"


def main():
    st.set_page_config(page_title="TalentAI — HR Intelligence", page_icon=":sparkles:", layout="wide")
    inject_global_css()

    if "results" not in st.session_state:
        st.session_state.results = []
    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = 0
    if "status_tab" not in st.session_state:
        st.session_state.status_tab = "All"
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "header_search" not in st.session_state:
        st.session_state.header_search = ""

    # ========== HEADER ==========
    search_val = st.session_state.header_search
    st.markdown(f"""
    <div class="talent-header">
        <div class="talent-logo">
            <div class="talent-logo-icon">&#10024;</div>
            <div class="talent-logo-text">
                <h1>TalentAI <span class="talent-badge">RECRUIT</span></h1>
            </div>
        </div>
        <div class="talent-search">
            <span class="talent-search-icon">&#128269;</span>
            <input type="text" placeholder="Search candidates by name, title, or skill..." value="{search_val}" />
        </div>
        <div class="talent-user">
            <div class="talent-user-info">
                <div class="talent-user-email">syedrabiaan@gmail.com</div>
                <div class="talent-user-role">Recruiting Manager</div>
            </div>
            <div class="talent-avatar">SR</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    header_search = st.text_input(
        "Search", placeholder="Search candidates...",
        label_visibility="collapsed", key="header_search_input",
    )
    if header_search != st.session_state.header_search:
        st.session_state.header_search = header_search
        st.session_state.search_query = header_search
        st.session_state.selected_idx = 0
        st.rerun()

    # ========== STATS BANNER ==========
    counts = {"Sourced": 0, "In Progress": 0, "Interview": 0, "Hired": 0}
    try:
        from ai.db import get_status_counts
        counts = get_status_counts()
    except Exception:
        if st.session_state.results:
            for r in st.session_state.results:
                rec = r.get("recommendation", "")
                if rec == "Hire":
                    counts["Hired"] += 1
                elif rec == "Interview":
                    counts["Interview"] += 1
                elif rec == "Reject":
                    counts["Sourced"] += 1
                else:
                    counts["In Progress"] += 1

    st.markdown(f"""
    <div class="stats-banner">
        <div class="stats-grid">
            <div class="stat-card stat-blue">
                <div class="stat-icon">&#128203;</div>
                <div><div class="stat-label">Sourced</div><div class="stat-value">{counts.get("Sourced", 0)}</div></div>
            </div>
            <div class="stat-card stat-purple">
                <div class="stat-icon">&#128200;</div>
                <div><div class="stat-label">In Progress</div><div class="stat-value">{counts.get("In Progress", 0)}</div></div>
            </div>
            <div class="stat-card stat-amber">
                <div class="stat-icon">&#128197;</div>
                <div><div class="stat-label">Interviews Scheduled</div><div class="stat-value">{counts.get("Interview", 0)}</div></div>
            </div>
            <div class="stat-card stat-emerald">
                <div class="stat-icon">&#9989;</div>
                <div><div class="stat-label">Hired / Offered</div><div class="stat-value">{counts.get("Hired", 0)}</div></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== UPLOAD SECTION ==========
    st.markdown("")
    jd_text, resume_tuples = render_uploader()

    if jd_text and resume_tuples:
        analyze_clicked = st.button("Analyze Resumes", type="primary", use_container_width=True)
        if analyze_clicked:
            resume_map = {name: text for name, text in resume_tuples}
            results: list[CandidateResult] = []
            progress = st.progress(0.0, text="Starting analysis...")
            status_box = st.empty()
            for idx, (name, text) in enumerate(resume_tuples):
                status_box.info(f"Analyzing **{name}** ({idx + 1}/{len(resume_tuples)})...")
                result = analyze_resume(name, text, jd_text)
                results.append(result)
                progress.progress((idx + 1) / len(resume_tuples), text=f"Completed {idx + 1}/{len(resume_tuples)}")
            status_box.success(f"Analysis complete — {len(results)} candidates processed.")
            st.session_state.results = [r.model_dump() for r in results]
            st.session_state.selected_idx = 0
            try:
                from ai.db import insert_job_description
                jd_row = insert_job_description(title=resume_tuples[0][0], raw_text=jd_text)
                persist_to_supabase(jd_row["id"], results, resume_map)
            except Exception:
                pass
            st.rerun()

    # ========== 3-COLUMN LAYOUT ==========
    if st.session_state.results:
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        all_candidates = list(st.session_state.results)
        try:
            from ai.db import fetch_history
            db_history = fetch_history(limit=100)
            if db_history:
                seen_names = {c["candidate_name"] for c in all_candidates}
                for db_c in db_history:
                    if db_c["candidate_name"] not in seen_names:
                        all_candidates.append(db_c)
                        seen_names.add(db_c["candidate_name"])
        except Exception:
            pass

        query = st.session_state.get("header_search", "").lower() or st.session_state.get("search_query", "").lower()
        tab = st.session_state.get("status_tab", "All")
        filtered = all_candidates
        if tab != "All":
            filtered = [c for c in filtered if c.get("status", "Sourced") == tab]
        if query:
            filtered = [c for c in filtered if query in c.get("candidate_name", "").lower() or query in c.get("summary", "").lower() or query in " ".join(c.get("matching_skills", []) or []).lower()]

        col_list, col_profile, col_chat = st.columns([4, 5, 3])

        with col_list:
            render_candidate_list(filtered, all_candidates)

        with col_profile:
            if filtered:
                sel_idx = min(st.session_state.selected_idx, len(filtered) - 1)
                render_candidate_profile(filtered[sel_idx])
            else:
                st.markdown('<div class="empty-state" style="padding:80px 16px;"><p style="font-size:48px;margin:0;">&#128100;</p><p style="font-weight:600;color:var(--slate-500);margin:12px 0 0 0;">No candidates match your filters</p><p style="font-size:11px;color:var(--slate-400);margin:4px 0 0 0;">Try a different search or pipeline tab.</p></div>', unsafe_allow_html=True)

        with col_chat:
            if filtered:
                sel_idx = min(st.session_state.selected_idx, len(filtered) - 1)
                render_ai_chat(filtered[sel_idx])
            else:
                st.markdown('<div class="empty-state" style="padding:40px 16px;"><p style="font-size:11px;color:var(--slate-400);">Select a candidate to activate the AI Co-Pilot.</p></div>', unsafe_allow_html=True)

    # ========== FOOTER ==========
    st.markdown("""
    <div class="talent-footer">
        <div style="max-width:1400px; margin:0 auto; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <p style="color:var(--slate-300); font-weight:700; font-size:11px; margin:0;">TalentAI HR Intelligence Engine &copy; 2026</p>
                <p style="font-size:10px; color:var(--slate-600); margin-top:3px;">Configured for syedrabiaan@gmail.com | SMIT Batch 9</p>
            </div>
            <div style="display:flex; gap:16px; align-items:center;">
                <span style="display:flex; align-items:center; gap:5px;">
                    <span class="pulse-dot"></span>
                    <span style="color:var(--slate-400);">Server Active</span>
                </span>
                <span style="display:flex; align-items:center; gap:5px;">
                    <span class="pulse-dot"></span>
                    <span style="color:var(--slate-400);">Supabase Connected</span>
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
