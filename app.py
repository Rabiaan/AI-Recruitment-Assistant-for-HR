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


def inject_global_css():
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
    /* Global */
    .stApp { font-family: 'Inter', sans-serif; background: #f8fafc; }
    .stApp header[data-testid="stHeader"] { background: #f8fafc; }

    /* Header */
    .talent-header {
        background: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 12px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 40;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 0;
    }
    .talent-logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .talent-logo-icon {
        width: 40px; height: 40px;
        border-radius: 12px;
        background: #4f46e5;
        display: flex; align-items: center; justify-content: center;
        color: white;
        font-size: 18px;
        box-shadow: 0 2px 8px rgba(79,70,229,0.25);
    }
    .talent-logo-text h1 {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .talent-badge {
        font-size: 10px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
        background: #e0e7ff;
        color: #4338ca;
    }
    .talent-subtitle {
        font-size: 11px;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
        margin: 0;
    }
    .talent-user {
        display: flex;
        align-items: center;
        gap: 10px;
        text-align: right;
    }
    .talent-user-name { font-size: 11px; font-weight: 700; color: #1e293b; }
    .talent-user-role { font-size: 9px; color: #4f46e5; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; }
    .talent-avatar {
        width: 36px; height: 36px;
        border-radius: 50%;
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        display: flex; align-items: center; justify-content: center;
        color: #4338ca;
        font-weight: 600;
        font-size: 13px;
    }

    /* Stats bar */
    .stats-bar {
        background: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 16px 24px;
        margin: 0 -1rem 1rem -1rem;
    }
    .stat-card {
        padding: 12px 16px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        border: 1px solid transparent;
    }
    .stat-icon {
        width: 40px; height: 40px;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px;
    }
    .stat-label { font-size: 11px; color: #94a3b8; }
    .stat-value { font-size: 1.2rem; font-weight: 700; color: #1e293b; }

    .stat-sourced { background: #eff6ff; border-color: #bfdbfe; }
    .stat-sourced .stat-icon { background: #dbeafe; color: #2563eb; }
    .stat-progress { background: #faf5ff; border-color: #e9d5ff; }
    .stat-progress .stat-icon { background: #f3e8ff; color: #9333ea; }
    .stat-interview { background: #fffbeb; border-color: #fde68a; }
    .stat-interview .stat-icon { background: #fef3c7; color: #d97706; }
    .stat-hired { background: #ecfdf5; border-color: #a7f3d0; }
    .stat-hired .stat-icon { background: #d1fae5; color: #059669; }

    /* Candidate cards */
    .candidate-card {
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #f1f5f9;
        cursor: pointer;
        transition: all 0.15s;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 8px;
        background: #ffffff;
    }
    .candidate-card:hover { background: #f8fafc; border-color: #e2e8f0; }
    .candidate-card.selected { background: #eef2ff; border-color: #c7d2fe; box-shadow: 0 1px 4px rgba(79,70,229,0.1); }
    .candidate-initials {
        width: 40px; height: 40px; min-width: 40px;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 12px;
    }
    .candidate-initials.default { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    .candidate-initials.active { background: #4f46e5; color: #ffffff; }
    .candidate-name { font-weight: 600; font-size: 13px; color: #1e293b; }
    .candidate-role { font-size: 11px; color: #94a3b8; margin-top: 2px; }
    .candidate-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
    .score-badge { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; }
    .score-high { background: #d1fae5; color: #065f46; }
    .score-mid { background: #fef3c7; color: #92400e; }
    .score-low { background: #fee2e2; color: #991b1b; }
    .status-badge { font-size: 10px; font-weight: 500; padding: 2px 8px; border-radius: 9999px; border: 1px solid; }
    .status-sourced { background: #f8fafc; color: #475569; border-color: #e2e8f0; }
    .status-in-progress { background: #faf5ff; color: #7c3aed; border-color: #e9d5ff; }
    .status-interview { background: #fffbeb; color: #d97706; border-color: #fde68a; }
    .status-hired { background: #ecfdf5; color: #059669; border-color: #a7f3d0; }

    /* Profile section */
    .profile-header {
        padding: 20px;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .profile-avatar-lg {
        width: 48px; height: 48px; border-radius: 16px;
        background: #f1f5f9; border: 1px solid #e2e8f0;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 14px; color: #475569;
    }
    .profile-metric {
        padding: 12px;
        background: #f8fafc;
        border-radius: 12px;
        border: 1px solid #f1f5f9;
        text-align: center;
    }
    .profile-metric-label { font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; }
    .profile-metric-value { font-size: 14px; font-weight: 700; color: #1e293b; margin-top: 4px; }

    /* Skill badges */
    .skill-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 500;
        margin: 2px;
    }
    .pill-match { background: #d1fae5; color: #065f46; }
    .pill-miss  { background: #fee2e2; color: #991b1b; }
    .pill-extra { background: #dbeafe; color: #1e40af; }

    /* Strengths/Gaps */
    .strengths-box { background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; padding: 12px; }
    .gaps-box { background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 12px; }
    .box-title { font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }

    /* Timeline */
    .timeline-item { position: relative; padding-left: 24px; margin-bottom: 16px; }
    .timeline-dot { position: absolute; left: 7px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: #4f46e5; }
    .timeline-line { position: absolute; left: 10px; top: 16px; bottom: -8px; width: 1px; background: #e2e8f0; }
    .timeline-company { font-size: 10px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; display: flex; justify-content: space-between; }
    .timeline-role { font-size: 12px; font-weight: 700; color: #1e293b; }
    .timeline-desc { font-size: 11px; color: #64748b; margin-top: 4px; line-height: 1.5; }

    /* AI Chat */
    .ai-panel { background: #0f172a; color: #e2e8f0; border-radius: 16px; padding: 16px; }
    .ai-header { display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid #1e293b; }
    .ai-msg-user { background: #4f46e5; color: white; border-radius: 12px 12px 4px 12px; padding: 10px 12px; max-width: 85%; font-size: 12px; }
    .ai-msg-ai { background: #1e293b; color: #e2e8f0; border-radius: 12px 12px 12px 4px; padding: 10px 12px; max-width: 85%; font-size: 12px; border: 1px solid #334155; }
    .ai-preset { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 8px 12px; font-size: 10px; color: #cbd5e1; cursor: pointer; display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 6px; }
    .ai-preset:hover { background: #334155; }

    /* Tabs */
    .pipeline-tabs { display: flex; background: #f1f5f9; border-radius: 12px; padding: 4px; gap: 4px; margin-bottom: 12px; }
    .pipeline-tab { flex: 1; text-align: center; padding: 8px; border-radius: 8px; font-size: 11px; font-weight: 500; cursor: pointer; border: none; background: transparent; color: #64748b; transition: all 0.15s; }
    .pipeline-tab.active { background: #ffffff; color: #1e293b; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

    /* Footer */
    .talent-footer {
        background: #020617; color: #475569; padding: 24px;
        border-top: 1px solid #1e293b;
        font-size: 11px; font-family: 'JetBrains Mono', monospace;
        margin: 2rem -1rem -1rem -1rem;
    }

    /* Section labels */
    .section-mono { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-weight: 600; }

    /* Empty state */
    .empty-state { text-align: center; padding: 40px; color: #94a3b8; }

    /* Hide Streamlit defaults */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    header[data-testid="stHeader"] { background: transparent; }
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
    except Exception as e:
        st.warning(f"DB persist skipped: {e}")
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


def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if name else "?"


def main():
    st.set_page_config(page_title="TalentAI — HR Intelligence", page_icon=":sparkles:", layout="wide")
    inject_global_css()

    # Initialize session state
    if "results" not in st.session_state:
        st.session_state.results = []
    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = 0
    if "status_tab" not in st.session_state:
        st.session_state.status_tab = "All"
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    # --- HEADER ---
    st.markdown("""
    <div class="talent-header">
        <div class="talent-logo">
            <div class="talent-logo-icon">&#10024;</div>
            <div class="talent-logo-text">
                <h1>TalentAI <span class="talent-badge">RECRUIT</span></h1>
                <p class="talent-subtitle">HR Intelligence Workspace</p>
            </div>
        </div>
        <div class="talent-user">
            <div>
                <p class="talent-user-name">syedrabiaan@gmail.com</p>
                <p class="talent-user-role">RECRUITING MANAGER</p>
            </div>
            <div class="talent-avatar">SR</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- STATS BAR ---
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
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 16px; max-width: 1200px; margin: 0 auto;">
            <div class="stat-card stat-sourced">
                <div class="stat-icon">&#128203;</div>
                <div><div class="stat-label">Sourced</div><div class="stat-value">{counts.get('Sourced', 0)}</div></div>
            </div>
            <div class="stat-card stat-progress">
                <div class="stat-icon">&#128200;</div>
                <div><div class="stat-label">In Progress</div><div class="stat-value">{counts.get('In Progress', 0)}</div></div>
            </div>
            <div class="stat-card stat-interview">
                <div class="stat-icon">&#128197;</div>
                <div><div class="stat-label">Interviews Scheduled</div><div class="stat-value">{counts.get('Interview', 0)}</div></div>
            </div>
            <div class="stat-card stat-hired">
                <div class="stat-icon">&#9989;</div>
                <div><div class="stat-label">Hired / Offered</div><div class="stat-value">{counts.get('Hired', 0)}</div></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- UPLOAD SECTION ---
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

    # --- MAIN 3-COLUMN GRID ---
    if st.session_state.results:
        st.markdown("---")

        # Load all results from DB for full pipeline view
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

        # Filter by status tab and search
        query = st.session_state.get("search_query", "").lower()
        tab = st.session_state.get("status_tab", "All")
        filtered = all_candidates
        if tab != "All":
            filtered = [c for c in filtered if c.get("status", "Sourced") == tab]
        if query:
            filtered = [c for c in filtered if query in c.get("candidate_name", "").lower() or query in c.get("summary", "").lower() or query in " ".join(c.get("matching_skills", []) or []).lower()]

        col_list, col_profile, col_chat = st.columns([4, 5, 3])

        # LEFT: Candidate List
        with col_list:
            render_candidate_list(filtered, all_candidates)

        # MIDDLE: Profile Detail
        with col_profile:
            if filtered:
                sel_idx = min(st.session_state.selected_idx, len(filtered) - 1)
                render_candidate_profile(filtered[sel_idx])
            else:
                st.markdown('<div class="empty-state"><p style="font-size:48px">&#128100;</p><p>No candidates match filters</p></div>', unsafe_allow_html=True)

        # RIGHT: AI Chat + Calendar
        with col_chat:
            if filtered:
                sel_idx = min(st.session_state.selected_idx, len(filtered) - 1)
                render_ai_chat(filtered[sel_idx])

    # --- FOOTER ---
    st.markdown("""
    <div class="talent-footer">
        <div style="max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <p style="color:#e2e8f0; font-weight:700; font-size:12px; margin:0;">TalentAI HR Dashboard Engine &copy; 2026</p>
                <p style="font-size:10px; color:#334155; margin-top:4px;">Configured for syedrabiaan@gmail.com | SMIT Batch 9</p>
            </div>
            <div style="display:flex; gap:16px;">
                <span style="display:flex; align-items:center; gap:4px;"><span style="width:6px; height:6px; border-radius:50%; background:#6366f1;"></span> Server Active</span>
                <span style="display:flex; align-items:center; gap:4px;"><span style="width:6px; height:6px; border-radius:50%; background:#10b981;"></span> Supabase Connected</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
