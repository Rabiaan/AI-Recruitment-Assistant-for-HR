from __future__ import annotations
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from components.uploader import render_upload_page
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
from utils.icons import icon

NOT_FOUND = "Not Found"

SYSTEM_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"


def inject_global_css():
    st.markdown(f"""
    <style>
    /* ===== RESET & BASE ===== */
    .stApp {{
        font-family: {SYSTEM_FONT};
        background: #ffffff;
        color: #0f172a;
    }}
    .stApp header[data-testid="stHeader"] {{ background: transparent; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }}
    section[data-testid="stSidebar"] {{ display: none; }}

    /* ===== VARIABLES ===== */
    :root {{
        --bg: #ffffff;
        --bg-section: #f9fafc;
        --border: #e5e7eb;
        --border-light: #f3f4f6;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --indigo-700: #4338ca;
        --indigo-600: #4f46e5;
        --indigo-500: #6366f1;
        --indigo-400: #818cf8;
        --indigo-100: #e0e7ff;
        --indigo-50: #eef2ff;
        --blue-500: #3b82f6;
        --blue-600: #2563eb;
        --blue-100: #dbeafe;
        --blue-50: #eff6ff;
        --purple-500: #a855f7;
        --purple-600: #9333ea;
        --purple-100: #f3e8ff;
        --purple-50: #faf5ff;
        --amber-500: #f59e0b;
        --amber-600: #d97706;
        --amber-100: #fef3c7;
        --amber-50: #fffbeb;
        --emerald-500: #10b981;
        --emerald-600: #059669;
        --emerald-100: #d1fae5;
        --emerald-50: #ecfdf5;
        --red-500: #ef4444;
        --red-600: #dc2626;
        --red-100: #fee2e2;
        -red-50: #fef2f2;
    }}

    /* ===== HEADER ===== */
    .nav-header {{
        background: #ffffff;
        border-bottom: 1px solid var(--border);
        padding: 0 24px;
        height: 56px;
        display: flex;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 999;
    }}
    .nav-logo {{
        display: flex; align-items: center; gap: 10px;
        min-width: 200px; text-decoration: none;
    }}
    .nav-logo-icon {{
        width: 32px; height: 32px; border-radius: 8px;
        background: linear-gradient(135deg, var(--indigo-500), var(--indigo-700));
        display: flex; align-items: center; justify-content: center;
        color: white;
    }}
    .nav-logo-text {{
        font-size: 15px; font-weight: 700; color: var(--text-primary);
        display: flex; align-items: center; gap: 8px;
    }}
    .nav-badge {{
        font-size: 9px; font-weight: 600; padding: 2px 7px;
        border-radius: 9999px; background: var(--indigo-100);
        color: var(--indigo-600); letter-spacing: 0.5px;
    }}

    /* Nav tabs */
    .nav-tabs {{
        display: flex; gap: 4px; margin-left: 32px;
    }}
    .nav-tab {{
        padding: 8px 16px; border-radius: 8px; font-size: 13px;
        font-weight: 500; color: var(--text-muted); cursor: pointer;
        border: none; background: transparent; transition: all 0.15s;
        display: flex; align-items: center; gap: 6px;
    }}
    .nav-tab:hover {{ background: var(--bg-section); color: var(--text-secondary); }}
    .nav-tab.active {{
        background: var(--indigo-50); color: var(--indigo-600);
        font-weight: 600;
    }}

    /* Search */
    .nav-search {{
        flex: 1; max-width: 420px; margin: 0 24px; position: relative;
    }}
    .nav-search input {{
        width: 100%; background: var(--bg-section);
        border: 1px solid var(--border); border-radius: 8px;
        padding: 8px 12px 8px 36px; color: var(--text-primary);
        font-size: 13px; font-family: {SYSTEM_FONT}; outline: none;
        transition: border-color 0.15s;
    }}
    .nav-search input:focus {{ border-color: var(--indigo-500); }}
    .nav-search input::placeholder {{ color: var(--text-muted); }}
    .nav-search-icon {{
        position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
        color: var(--text-muted);
    }}

    /* User */
    .nav-user {{
        display: flex; align-items: center; gap: 10px;
        margin-left: auto;
    }}
    .nav-user-info {{ text-align: right; }}
    .nav-user-email {{ font-size: 11px; font-weight: 600; color: var(--text-primary); }}
    .nav-user-role {{
        font-size: 9px; color: var(--indigo-500);
        font-family: {MONO_FONT}; letter-spacing: 1px; text-transform: uppercase;
    }}
    .nav-avatar {{
        width: 32px; height: 32px; border-radius: 50%;
        background: var(--indigo-600); color: white;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 11px;
    }}

    /* ===== STATS BANNER ===== */
    .stats-bar {{
        background: var(--bg); border-bottom: 1px solid var(--border);
        padding: 16px 24px;
    }}
    .stats-grid {{
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    }}
    .stat-card {{
        padding: 14px 16px; border-radius: 12px;
        display: flex; align-items: center; gap: 12px;
        border: 1px solid transparent; background: var(--bg-section);
    }}
    .stat-icon-wrap {{
        width: 40px; height: 40px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
    }}
    .stat-label {{ font-size: 11px; color: var(--text-muted); font-weight: 500; }}
    .stat-value {{ font-size: 22px; font-weight: 800; color: var(--text-primary); line-height: 1.2; }}

    .stat-blue .stat-icon-wrap {{ background: var(--blue-50); color: var(--blue-500); }}
    .stat-purple .stat-icon-wrap {{ background: var(--purple-50); color: var(--purple-500); }}
    .stat-amber .stat-icon-wrap {{ background: var(--amber-50); color: var(--amber-500); }}
    .stat-emerald .stat-icon-wrap {{ background: var(--emerald-50); color: var(--emerald-500); }}

    /* ===== SECTION UTILITIES ===== */
    .section-label {{
        font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px;
        color: var(--text-muted); font-family: {MONO_FONT}; font-weight: 600;
    }}
    .section-card {{
        background: var(--bg-section); border: 1px solid var(--border-light);
        border-radius: 12px; padding: 16px; margin-bottom: 12px;
    }}

    /* ===== PIPELINE TABS ===== */
    .pipeline-tabs {{
        display: flex; background: var(--bg-section);
        border-radius: 10px; padding: 3px; gap: 3px; margin-bottom: 12px;
    }}
    .pipeline-tab {{
        flex: 1; text-align: center; padding: 7px 4px;
        border-radius: 8px; font-size: 11px; font-weight: 500;
        cursor: pointer; border: none; background: transparent;
        color: var(--text-muted); transition: all 0.15s;
    }}
    .pipeline-tab.active {{
        background: #ffffff; color: var(--text-primary);
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}

    /* ===== CANDIDATE CARDS ===== */
    .candidate-card {{
        padding: 12px 14px; border-radius: 10px;
        border: 1px solid var(--border-light); cursor: pointer;
        transition: all 0.15s; display: flex; align-items: flex-start;
        gap: 10px; margin-bottom: 6px; background: #ffffff;
    }}
    .candidate-card:hover {{ border-color: var(--border); }}
    .candidate-card.selected {{
        border-color: var(--indigo-400);
        box-shadow: 0 0 0 1px var(--indigo-100);
        background: var(--indigo-50);
    }}
    .initials-badge {{
        width: 40px; height: 40px; min-width: 40px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 13px; color: white;
    }}
    .candidate-name {{ font-weight: 600; font-size: 13px; color: var(--text-primary); }}
    .candidate-title {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; }}

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
    .pill-sourced {{ background: var(--bg-section); color: var(--text-secondary); border-color: var(--border); }}
    .pill-in-progress {{ background: var(--purple-50); color: var(--purple-600); border-color: #e9d5ff; }}
    .pill-interview {{ background: var(--amber-50); color: var(--amber-600); border-color: #fde68a; }}
    .pill-hired {{ background: var(--emerald-50); color: var(--emerald-600); border-color: #a7f3d0; }}

    /* ===== PROFILE ===== */
    .profile-header {{
        padding: 16px 20px; border-bottom: 1px solid var(--border-light);
        display: flex; align-items: center; justify-content: space-between;
    }}
    .profile-avatar-lg {{
        width: 48px; height: 48px; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 16px; color: white;
    }}
    .metric-card {{
        padding: 14px; background: #ffffff; border-radius: 10px;
        border: 1px solid var(--border-light); text-align: center;
    }}
    .metric-label {{
        font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px;
        color: var(--text-muted); font-family: {MONO_FONT}; font-weight: 600;
    }}
    .metric-value {{ font-size: 18px; font-weight: 800; color: var(--text-primary); margin-top: 4px; }}

    /* ===== SKILL TAGS ===== */
    .skill-tag {{
        display: inline-block; padding: 5px 12px; border-radius: 6px;
        font-size: 12px; font-weight: 500; margin: 3px;
    }}
    .tag-match {{ background: var(--emerald-50); color: var(--emerald-600); border: 1px solid #a7f3d0; }}
    .tag-miss {{ background: var(--red-50); color: var(--red-600); border: 1px solid #fecaca; }}
    .tag-extra {{ background: var(--blue-50); color: var(--blue-600); border: 1px solid #bfdbfe; }}

    /* ===== STRENGTHS / GAPS ===== */
    .strengths-card {{
        background: var(--emerald-50); border: 1px solid #a7f3d0;
        border-radius: 10px; padding: 14px;
    }}
    .gaps-card {{
        background: var(--red-50); border: 1px solid #fecaca;
        border-radius: 10px; padding: 14px;
    }}
    .card-title {{ font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }}

    /* ===== TIMELINE ===== */
    .tl-item {{ position: relative; padding-left: 28px; margin-bottom: 20px; }}
    .tl-dot {{
        position: absolute; left: 6px; top: 5px;
        width: 10px; height: 10px; border-radius: 50%;
        border: 2px solid var(--indigo-500); background: white;
    }}
    .tl-line {{
        position: absolute; left: 10px; top: 20px;
        bottom: -12px; width: 1px; background: var(--border);
    }}
    .tl-meta {{
        font-size: 10px; color: var(--text-muted);
        font-family: {MONO_FONT}; display: flex; justify-content: space-between;
    }}
    .tl-role {{ font-size: 13px; font-weight: 700; color: var(--text-primary); margin-top: 2px; }}
    .tl-desc {{ font-size: 11px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }}

    /* ===== PROGRESS BAR ===== */
    .pref-bar-bg {{
        width: 100%; height: 10px; border-radius: 9999px;
        background: var(--border-light); overflow: hidden; display: flex;
    }}
    .pref-bar-fill {{ height: 100%; }}
    .pref-legend {{ display: flex; gap: 14px; margin-top: 8px; flex-wrap: wrap; }}
    .pref-legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--text-secondary); }}
    .pref-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}

    /* ===== AI CHAT ===== */
    .ai-panel {{
        background: #0f172a; color: #e2e8f0;
        border-radius: 14px; padding: 16px; border: 1px solid #1e293b;
    }}
    .ai-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 12px; border-bottom: 1px solid #1e293b;
        margin-bottom: 12px;
    }}
    .ai-msg-user {{
        background: var(--indigo-600); color: white;
        border-radius: 12px 12px 4px 12px; padding: 10px 12px;
        max-width: 90%; font-size: 12px;
    }}
    .ai-msg-ai {{
        background: #1e293b; color: #e2e8f0;
        border-radius: 12px 12px 12px 4px; padding: 10px 12px;
        max-width: 90%; font-size: 12px; border: 1px solid #334155;
    }}

    /* ===== CALENDAR ===== */
    .cal-card {{
        background: #ffffff; border: 1px solid var(--border);
        border-radius: 28px; padding: 22px 20px 18px;
        box-shadow: 0 20px 40px -12px rgba(20,20,40,0.08);
    }}
    .cal-header {{
        display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    }}
    .cal-header .month {{ font-size: 15px; font-weight: 600; color: var(--text-primary); }}
    .cal-nav {{
        width: 26px; height: 26px; border-radius: 50%; border: none;
        background: transparent; color: #c7cbd3; font-size: 16px;
        cursor: pointer; display: flex; align-items: center; justify-content: center;
    }}
    .cal-nav:hover {{ background: #f0f1f4; color: #a6acb8; }}
    .cal-weekdays {{
        display: grid; grid-template-columns: repeat(7, 1fr);
        text-align: center; font-size: 11px; color: #c7cbd3;
        font-weight: 600; margin-bottom: 6px;
    }}
    .cal-days {{ display: grid; grid-template-columns: repeat(7, 1fr); row-gap: 6px; }}
    .cal-day {{
        position: relative; height: 34px; display: flex; align-items: center;
        justify-content: center; font-size: 13px; color: var(--text-primary);
    }}
    .cal-day.muted {{ color: #c7cbd3; }}
    .cal-day.weekend {{ color: #ff5a6e; }}
    .cal-day.weekend.muted {{ color: #f3c3c9; }}
    .cal-day.today {{
        background: #3f6bff; color: white; border-radius: 50%;
        width: 30px; height: 30px; font-weight: 600;
    }}
    .cal-day .dot {{
        position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%);
        width: 3px; height: 3px; border-radius: 50%; background: #3f6bff;
        box-shadow: 5px 0 0 #3f6bff, -5px 0 0 #3f6bff;
    }}

    /* Agenda */
    .cal-agenda {{ margin-top: 18px; padding-top: 16px; border-top: 1px solid #f0f1f4; display: flex; flex-direction: column; gap: 14px; }}
    .cal-event {{ display: flex; align-items: center; gap: 12px; }}
    .cal-bar {{ width: 3px; align-self: stretch; border-radius: 2px; flex-shrink: 0; }}
    .cal-bar.orange {{ background: #f5a623; }}
    .cal-bar.green {{ background: #3ecf8e; }}
    .cal-bar.blue {{ background: #3f6bff; }}
    .cal-bar.red {{ background: #ff5a6e; }}
    .cal-datetime {{ width: 56px; flex-shrink: 0; font-size: 11px; line-height: 1.4; color: #c7cbd3; font-weight: 600; }}
    .cal-info {{ flex: 1; min-width: 0; }}
    .cal-event-role {{ font-size: 11px; color: #a6acb8; margin-bottom: 2px; }}
    .cal-event-title {{ font-size: 14px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .cal-call-icon {{
        width: 26px; height: 26px; border-radius: 7px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
    }}
    .cal-call-icon.meet {{ background: #eaf6ec; }}
    .cal-call-icon.zoom {{ background: #e8effe; }}
    .cal-call-icon svg {{ width: 15px; height: 15px; }}

    /* ===== UPLOAD PAGE ===== */
    .upload-page {{
        min-height: 100vh; background: var(--bg-section);
        display: flex; align-items: center; justify-content: center;
        padding: 40px 24px;
    }}
    .upload-card {{
        background: white; border-radius: 20px; padding: 40px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        max-width: 800px; width: 100%;
    }}

    /* ===== FOOTER ===== */
    .talent-footer {{
        background: #020617; color: #475569;
        padding: 20px 24px; border-top: 1px solid #1e293b;
        font-size: 10px; font-family: {MONO_FONT};
    }}

    /* ===== EMPTY STATE ===== */
    .empty-state {{ text-align: center; padding: 40px; color: var(--text-muted); }}

    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
    .pulse-dot {{
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--emerald-500); animation: pulse 2s infinite;
        display: inline-block;
    }}

    /* Hide Streamlit elements */
    [data-testid="stToolbar"] {{ display: none; }}
    [data-testid="stDecoration"] {{ display: none; }}
    div[data-testid="stStatusWidget"] {{ display: none; }}
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


def render_header():
    page = st.session_state.get("page", "dashboard")
    upload_active = "active" if page == "upload" else ""
    dash_active = "active" if page == "dashboard" else ""

    search_val = st.session_state.get("header_search", "")
    st.markdown(f"""
    <div class="nav-header">
        <div class="nav-logo">
            <div class="nav-logo-icon">{icon("sparkles", 16, "white")}</div>
            <div class="nav-logo-text">TalentAI <span class="nav-badge">RECRUIT</span></div>
        </div>
        <div class="nav-tabs">
            <button class="nav-tab {dash_active}" id="nav_dash">
                {icon("home", 14)} Dashboard
            </button>
            <button class="nav-tab {upload_active}" id="nav_upload">
                {icon("upload", 14)} Upload
            </button>
        </div>
        <div class="nav-search">
            <span class="nav-search-icon">{icon("search", 14)}</span>
            <input type="text" placeholder="Search by name, title, or skill..." value="{search_val}" />
        </div>
        <div class="nav-user">
            <div class="nav-user-info">
                <div class="nav-user-email">syedrabiaan@gmail.com</div>
                <div class="nav-user-role">Recruiting Manager</div>
            </div>
            <div class="nav-avatar">SR</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_cols = st.columns([1, 1, 5, 2])
    with nav_cols[0]:
        if st.button("Dashboard", key="nav_btn_dash", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with nav_cols[1]:
        if st.button("Upload", key="nav_btn_upload", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()

    search_input = st.text_input(
        "Search", label_visibility="collapsed", key="header_search_widget",
        placeholder="Search candidates...", value=search_val,
    )
    if search_input != st.session_state.get("header_search", ""):
        st.session_state.header_search = search_input
        st.session_state.search_query = search_input
        st.session_state.selected_idx = 0
        st.rerun()


def render_stats():
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
    <div class="stats-bar">
        <div class="stats-grid">
            <div class="stat-card stat-blue">
                <div class="stat-icon-wrap">{icon("inbox", 18, "#3b82f6")}</div>
                <div><div class="stat-label">Sourced</div><div class="stat-value">{counts.get("Sourced", 0)}</div></div>
            </div>
            <div class="stat-card stat-purple">
                <div class="stat-icon-wrap">{icon("trending-up", 18, "#a855f7")}</div>
                <div><div class="stat-label">In Progress</div><div class="stat-value">{counts.get("In Progress", 0)}</div></div>
            </div>
            <div class="stat-card stat-amber">
                <div class="stat-icon-wrap">{icon("calendar", 18, "#f59e0b")}</div>
                <div><div class="stat-label">Interviews Scheduled</div><div class="stat-value">{counts.get("Interview", 0)}</div></div>
            </div>
            <div class="stat-card stat-emerald">
                <div class="stat-icon-wrap">{icon("check-circle", 18, "#10b981")}</div>
                <div><div class="stat-label">Hired / Offered</div><div class="stat-value">{counts.get("Hired", 0)}</div></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_dashboard():
    all_candidates = list(st.session_state.results)
    try:
        from ai.db import fetch_history
        db_history = fetch_history(limit=100)
        if db_history:
            seen = {c["candidate_name"] for c in all_candidates}
            for db_c in db_history:
                if db_c["candidate_name"] not in seen:
                    all_candidates.append(db_c)
                    seen.add(db_c["candidate_name"])
    except Exception:
        pass

    query = st.session_state.get("search_query", "").lower()
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
            st.markdown(f"""
            <div class="empty-state" style="padding:80px 16px;">
                {icon("users", 48, "#94a3b8")}
                <p style="font-weight:600;color:#64748b;margin:12px 0 0 0;">No candidates found</p>
                <p style="font-size:11px;color:#94a3b8;margin:4px 0 0 0;">Upload resumes to get started.</p>
            </div>
            """, unsafe_allow_html=True)

    with col_chat:
        if filtered:
            sel_idx = min(st.session_state.selected_idx, len(filtered) - 1)
            render_ai_chat(filtered[sel_idx])
        else:
            st.markdown(f"""
            <div class="empty-state" style="padding:40px 16px;">
                {icon("message-square", 24, "#94a3b8")}
                <p style="font-size:11px;color:#94a3b8;margin:8px 0 0 0;">Select a candidate to activate the AI Co-Pilot.</p>
            </div>
            """, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="TalentAI", page_icon=None, layout="wide")
    inject_global_css()

    for key, default in [("results", []), ("selected_idx", 0), ("status_tab", "All"),
                          ("search_query", ""), ("header_search", ""), ("page", "dashboard")]:
        if key not in st.session_state:
            st.session_state[key] = default

    render_header()

    page = st.session_state.page

    if page == "upload":
        jd_text, resume_tuples = render_upload_page()
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
                st.session_state.page = "dashboard"
                st.rerun()
    else:
        if st.session_state.results:
            render_stats()
            render_dashboard()
        else:
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                        min-height:60vh;gap:16px;color:#94a3b8;">
                {icon("upload", 48, "#cbd5e1")}
                <p style="font-size:16px;font-weight:600;color:#475569;margin:0;">No data yet</p>
                <p style="font-size:13px;color:#94a3b8;margin:0;">Upload a Job Description and Resumes to begin analysis.</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="talent-footer">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p style="color:#e2e8f0;font-weight:700;font-size:11px;margin:0;">TalentAI HR Intelligence Engine</p>
                <p style="font-size:10px;color:#475569;margin-top:3px;">SMIT Batch 9 | syedrabiaan@gmail.com</p>
            </div>
            <div style="display:flex;gap:16px;align-items:center;">
                <span style="display:flex;align-items:center;gap:5px;">
                    <span class="pulse-dot"></span>
                    <span style="color:#94a3b8;">Server Active</span>
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
