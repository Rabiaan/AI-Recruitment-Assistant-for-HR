from __future__ import annotations
import os
from datetime import datetime

import streamlit as st

try:
    from utils.icons import icon
except ImportError:
    def icon(name: str, size: int = 16, color: str = "currentColor") -> str:
        return ""

try:
    from ai.chains import build_summary_chain, build_skill_match_chain, build_score_chain, build_hr_chain, build_interview_questions_chain, parse_score, parse_recommendation, parse_skill_lists, parse_interview_questions, _invoke_with_retry
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from utils.parser import CandidateResult, build_candidate_result
except ImportError:
    CandidateResult = None
    build_candidate_result = None

try:
    from utils.pdf_reader import extract_text as pdf_extract
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

SYSTEM_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"

STATUS_OPTIONS = ["Sourced", "In Progress", "Interview", "Hired"]

# ============================================================
# CSS
# ============================================================

def inject_global_css():
    st.markdown(f"""
    <style>
    .stApp {{ font-family: {SYSTEM_FONT}; background: #ffffff; color: #0f172a; }}
    .stApp header[data-testid="stHeader"] {{ background: transparent; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    .block-container {{ padding-top: 0 !important; padding-bottom: 0 !important; padding-left: 0 !important; padding-right: 0 !important; max-width: 100% !important; width: 100% !important; }}
    section[data-testid="stSidebar"] {{ display: none; }}
    [data-testid="stToolbar"] {{ display: none; }}
    [data-testid="stDecoration"] {{ display: none; }}
    div[data-testid="stStatusWidget"] {{ display: none; }}

    :root {{
        --bg-section: #f9fafc; --border: #e5e7eb; --border-light: #f3f4f6;
        --text-primary: #0f172a; --text-secondary: #475569; --text-muted: #94a3b8;
        --indigo-700: #4338ca; --indigo-600: #4f46e5; --indigo-500: #6366f1;
        --indigo-400: #818cf8; --indigo-100: #e0e7ff; --indigo-50: #eef2ff;
        --blue-500: #3b82f6; --blue-100: #dbeafe; --blue-50: #eff6ff;
        --purple-500: #a855f7; --purple-100: #f3e8ff; --purple-50: #faf5ff;
        --amber-500: #f59e0b; --amber-100: #fef3c7; --amber-50: #fffbeb;
        --emerald-500: #10b981; --emerald-600: #059669; --emerald-100: #d1fae5; --emerald-50: #ecfdf5;
        --red-500: #ef4444; --red-600: #dc2626; --red-100: #fee2e2; --red-50: #fef2f2;
    }}

    /* Header */
    .nav-header {{ background:#fff; border-bottom:1px solid var(--border); padding:14px 24px;
        display:flex; align-items:center; gap:16px; }}
    .nav-logo {{ display:flex; align-items:center; gap:10px; }}
    .nav-logo-icon {{ width:36px; height:36px; border-radius:10px;
        background: linear-gradient(135deg, var(--indigo-500), var(--indigo-700));
        display:flex; align-items:center; justify-content:center; color:white; }}
    .nav-logo-text {{ font-size:18px; font-weight:700; color:var(--text-primary); display:flex; align-items:center; gap:8px; }}
    .nav-badge {{ font-size:9px; font-weight:600; padding:2px 8px; border-radius:9999px;
        background:var(--indigo-100); color:var(--indigo-600); letter-spacing:0.5px; }}
    .nav-subtitle {{ font-size:11px; color:var(--text-muted); font-family:{MONO_FONT}; margin-top:1px; }}
    .nav-user-info {{ text-align:right; }}
    .nav-user-email {{ font-size:12px; font-weight:700; color:var(--text-primary); }}
    .nav-user-role {{ font-size:9px; color:var(--indigo-500); font-family:{MONO_FONT}; letter-spacing:1px; text-transform:uppercase; }}
    .nav-avatar {{ width:36px; height:36px; border-radius:50%; background:var(--indigo-600); color:white;
        display:flex; align-items:center; justify-content:center; font-weight:700; font-size:12px; }}

    /* Stats */
    .stats-bar {{ background:#fff; border-bottom:1px solid var(--border); padding:14px 24px 18px; }}
    .stats-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
    .stat-card {{ padding:14px 16px; border-radius:14px; display:flex; align-items:center; gap:12px; background:var(--bg-section); }}
    .stat-icon-wrap {{ width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; }}
    .stat-label {{ font-size:11px; color:var(--text-muted); font-weight:500; }}
    .stat-value {{ font-size:22px; font-weight:800; color:var(--text-primary); line-height:1.2; }}
    .stat-blue .stat-icon-wrap {{ background:var(--blue-50); color:var(--blue-500); }}
    .stat-purple .stat-icon-wrap {{ background:var(--purple-50); color:var(--purple-500); }}
    .stat-amber .stat-icon-wrap {{ background:var(--amber-50); color:var(--amber-500); }}
    .stat-emerald .stat-icon-wrap {{ background:var(--emerald-50); color:var(--emerald-500); }}

    /* Candidate list */
    .panel-card {{ background:#fff; border:1px solid var(--border-light); border-radius:16px; padding:16px; }}
    .panel-header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }}
    .panel-title {{ font-weight:700; color:var(--text-primary); display:flex; align-items:center; gap:8px; font-size:14px; }}
    .count-badge {{ background:var(--bg-section); color:var(--text-secondary); font-size:11px; padding:2px 9px; border-radius:9999px; }}
    .no-photos {{ font-size:10px; color:var(--text-muted); font-family:{MONO_FONT}; }}

    .initials-badge {{ width:38px; height:38px; min-width:38px; border-radius:10px;
        display:flex; align-items:center; justify-content:center; font-weight:700; font-size:12px;
        background: var(--indigo-100); color: var(--indigo-700); }}
    .initials-badge.selected {{ background:var(--indigo-600); color:white; }}

    .score-pill {{ font-size:10px; font-weight:700; padding:3px 8px; border-radius:6px; font-family:{MONO_FONT}; white-space:nowrap; }}
    .score-high {{ background:var(--emerald-100); color:var(--emerald-600); }}
    .score-mid {{ background:var(--amber-100); color:var(--amber-600); }}

    .pipeline-pill {{ font-size:9px; font-weight:600; padding:2px 8px; border-radius:9999px; border:1px solid; letter-spacing:0.3px; display:inline-block; }}
    .pill-sourced {{ background:var(--bg-section); color:var(--text-secondary); border-color:var(--border); }}
    .pill-in-progress {{ background:var(--purple-50); color:#9333ea; border-color:#e9d5ff; }}
    .pill-interview {{ background:var(--amber-50); color:#d97706; border-color:#fde68a; }}
    .pill-hired {{ background:var(--emerald-50); color:var(--emerald-600); border-color:#a7f3d0; }}

    /* Profile */
    .metric-card {{ padding:14px; background:var(--bg-section); border-radius:12px; text-align:center; }}
    .metric-label {{ font-size:9px; text-transform:uppercase; letter-spacing:1.5px; color:var(--text-muted); font-family:{MONO_FONT}; font-weight:600; }}
    .metric-value {{ font-size:16px; font-weight:800; color:var(--text-primary); margin-top:4px; }}
    .metric-value.accent {{ color:var(--indigo-700); }}

    .skill-tag {{ display:inline-block; padding:5px 12px; border-radius:8px; font-size:12px; font-weight:500;
        margin:3px; background:var(--bg-section); color:var(--text-secondary); border:1px solid var(--border-light); }}

    .strengths-card {{ background:var(--emerald-50); border:1px solid #a7f3d0; border-radius:12px; padding:14px; }}
    .gaps-card {{ background:var(--red-50); border:1px solid #fecaca; border-radius:12px; padding:14px; }}
    .card-title {{ font-size:11px; font-weight:700; display:flex; align-items:center; gap:6px; margin-bottom:8px; }}
    .card-title.g {{ color:#065f46; }}
    .card-title.r {{ color:#991b1b; }}

    .tl-item {{ position:relative; padding-left:26px; margin-bottom:16px; }}
    .tl-dot {{ position:absolute; left:5px; top:4px; width:9px; height:9px; border-radius:50%; border:2px solid var(--indigo-500); background:white; }}
    .tl-meta {{ font-size:10px; color:var(--text-muted); font-family:{MONO_FONT}; display:flex; justify-content:space-between; }}
    .tl-role {{ font-size:13px; font-weight:700; color:var(--text-primary); margin-top:2px; }}
    .tl-desc {{ font-size:11px; color:var(--text-secondary); margin-top:4px; line-height:1.5; }}

    .pref-bar-bg {{ width:100%; height:8px; border-radius:9999px; background:var(--border-light); overflow:hidden; display:flex; margin-top:8px; }}
    .pref-bar-fill {{ height:100%; }}

    /* AI panel */
    .ai-panel {{ background:#0f172a; color:#e2e8f0; border-radius:16px; padding:16px; border:1px solid #1e293b; }}
    .ai-header {{ display:flex; align-items:center; justify-content:space-between; padding-bottom:10px; border-bottom:1px solid #1e293b; margin-bottom:10px; }}
    .ai-title {{ font-size:12px; font-weight:700; }}
    .ai-sub {{ font-size:9px; color:#94a3b8; font-family:{MONO_FONT}; }}
    .ai-msg-user {{ background:var(--indigo-600); color:white; border-radius:12px 12px 4px 12px; padding:9px 12px; max-width:92%; font-size:12px; margin-left:auto; }}
    .ai-msg-ai {{ background:#1e293b; color:#e2e8f0; border-radius:12px 12px 12px 4px; padding:9px 12px; max-width:92%; font-size:12px; border:1px solid #334155; }}
    .ai-empty {{ text-align:center; padding:14px 4px; color:#94a3b8; font-size:11px; }}

    /* Calendar / agenda panel */
    .agenda-card {{ background:#fff; border:1px solid var(--border-light); border-radius:16px; padding:14px; }}
    .agenda-header {{ display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--border-light); padding-bottom:10px; margin-bottom:10px; }}
    .agenda-title {{ font-size:11px; font-weight:700; color:var(--text-primary); text-transform:uppercase; font-family:{MONO_FONT}; display:flex; align-items:center; gap:6px; }}
    .agenda-date {{ font-size:10px; font-weight:700; background:var(--bg-section); color:var(--text-muted); padding:3px 8px; border-radius:9999px; }}
    .agenda-event {{ background:var(--bg-section); border-radius:12px; padding:9px 10px; margin-bottom:8px; display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }}
    .agenda-time {{ font-family:{MONO_FONT}; font-size:10px; color:var(--indigo-600); font-weight:700; }}
    .agenda-type {{ font-size:9px; padding:1px 7px; border-radius:6px; font-weight:600; margin-left:6px; }}
    .agenda-type.Interview {{ background:var(--amber-100); color:#92400e; }}
    .agenda-type.Meeting {{ background:var(--blue-100); color:#1e40af; }}
    .agenda-event-title {{ font-size:11px; font-weight:700; color:var(--text-primary); margin-top:2px; }}
    .agenda-event-with {{ font-size:10px; color:var(--text-muted); margin-top:1px; }}

    /* Footer */
    .talent-footer {{ background:#020617; color:#475569; padding:16px 24px; margin-top:16px; font-size:10px; font-family:{MONO_FONT};
        display:flex; justify-content:space-between; align-items:center; border-radius:16px 16px 0 0; }}
    @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
    .pulse-dot {{ width:6px; height:6px; border-radius:50%; background:var(--emerald-500); animation:pulse 2s infinite; display:inline-block; }}

    div[data-testid="stButton"] > button {{ border-radius:10px; }}

    /* Fix buttons in dark containers */
    .ai-panel div[data-testid="stButton"] > button {{
        background: rgba(255,255,255,0.1) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }}
    .ai-panel div[data-testid="stButton"] > button:hover {{
        background: rgba(255,255,255,0.2) !important;
        color: #ffffff !important;
    }}
    .talent-footer div[data-testid="stButton"] > button {{
        background: rgba(255,255,255,0.08) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }}

    /* Fix Select buttons in candidate cards — ensure readable */
    div[data-testid="stForm"] div[data-testid="stButton"] > button {{
        font-size: 11px;
    }}

    /* Upload page */
    .upload-hero {{ text-align:center; padding:48px 0 32px; }}
    .upload-hero-icon {{ width:64px; height:64px; border-radius:18px; background:linear-gradient(135deg, var(--indigo-500), var(--indigo-700));
        display:inline-flex; align-items:center; justify-content:center; margin-bottom:16px; }}
    .upload-hero h2 {{ font-size:22px; font-weight:800; color:var(--text-primary); margin:0; }}
    .upload-hero p {{ font-size:13px; color:var(--text-muted); margin:6px 0 0; }}
    .upload-zone {{ background:#fff; border:2px dashed var(--border); border-radius:16px; padding:32px; text-align:center;
        transition:border-color 0.2s, background 0.2s; cursor:pointer; }}
    .upload-zone:hover {{ border-color:var(--indigo-400); background:var(--indigo-50); }}
    .upload-zone-label {{ font-size:13px; font-weight:600; color:var(--text-primary); margin-bottom:4px; }}
    .upload-zone-hint {{ font-size:11px; color:var(--text-muted); }}
    .upload-file-row {{ display:flex; align-items:center; gap:10px; padding:10px 14px; background:var(--bg-section);
        border-radius:10px; margin-bottom:6px; border:1px solid var(--border-light); }}
    .upload-file-name {{ font-size:12px; font-weight:600; color:var(--text-primary); flex:1; }}
    .upload-file-size {{ font-size:10px; color:var(--text-muted); font-family:{MONO_FONT}; }}
    .upload-section-title {{ font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:var(--text-muted);
        font-family:{MONO_FONT}; font-weight:600; margin-bottom:10px; display:flex; align-items:center; gap:6px; }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def get_initials(name: str) -> str:
    parts = name.split(" ")
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper()


def status_slug(status: str) -> str:
    return status.lower().replace(" ", "-")


def find_candidate(cid: str):
    for c in st.session_state.candidates:
        if c["id"] == cid:
            return c
    return st.session_state.candidates[0]


# ============================================================
# HEADER
# ============================================================

def render_header():
    page = st.session_state.get("page", "dashboard")

    # Logo + Nav buttons in one row
    logo_col, nav_col, user_col = st.columns([2, 3, 5])
    with logo_col:
        st.markdown(f"""
        <div class="nav-logo" style="margin-top:8px;">
            <div class="nav-logo-icon">{icon("sparkles", 18, "white")}</div>
            <div>
                <div class="nav-logo-text">TalentAI <span class="nav-badge">RECRUIT</span></div>
                <div class="nav-subtitle">HR Intelligence Workspace</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with nav_col:
        dash_type = "primary" if page == "dashboard" else "secondary"
        upload_type = "primary" if page == "upload" else "secondary"
        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("Dashboard", key="nav_dashboard_btn", use_container_width=True, type=dash_type):
                st.session_state.page = "dashboard"
                st.rerun()
        with nav2:
            if st.button("Upload", key="nav_upload_btn_header", use_container_width=True, type=upload_type):
                st.session_state.page = "upload"
                st.rerun()
    with user_col:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; justify-content:flex-end; margin-top:8px;">
            <div class="nav-user-info">
                <div class="nav-user-email">syedrabiaan@gmail.com</div>
                <div class="nav-user-role">Recruiting Manager</div>
            </div>
            <div class="nav-avatar">SR</div>
        </div>
        """, unsafe_allow_html=True)

    if page == "dashboard":
        col_search, col_add, col_spacer = st.columns([5, 2, 3])
        with col_search:
            query = st.text_input(
                "Search", key="search_query_widget", label_visibility="collapsed",
                placeholder="Search by candidate name, role, or skill...",
                value=st.session_state.search_query,
            )
            if query != st.session_state.search_query:
                st.session_state.search_query = query
                st.rerun()
        with col_add:
            if st.button("Add Candidate", key="open_add_modal", use_container_width=True, type="primary"):
                add_candidate_dialog()


# ============================================================
# STATS PANEL
# ============================================================

def render_stats():
    candidates = st.session_state.candidates
    counts = {s: len([c for c in candidates if c["status"] == s]) for s in STATUS_OPTIONS}
    st.markdown(f"""
    <div class="stats-bar">
      <div class="stats-grid">
        <div class="stat-card stat-blue">
            <div class="stat-icon-wrap">{icon("layers", 18, "#3b82f6")}</div>
            <div><div class="stat-label">Sourced</div><div class="stat-value">{counts["Sourced"]}</div></div>
        </div>
        <div class="stat-card stat-purple">
            <div class="stat-icon-wrap">{icon("trending-up", 18, "#a855f7")}</div>
            <div><div class="stat-label">In Progress</div><div class="stat-value">{counts["In Progress"]}</div></div>
        </div>
        <div class="stat-card stat-amber">
            <div class="stat-icon-wrap">{icon("calendar", 18, "#f59e0b")}</div>
            <div><div class="stat-label">Interviews Scheduled</div><div class="stat-value">{counts["Interview"]}</div></div>
        </div>
        <div class="stat-card stat-emerald">
            <div class="stat-icon-wrap">{icon("user-check", 18, "#10b981")}</div>
            <div><div class="stat-label">Hired / Offered</div><div class="stat-value">{counts["Hired"]}</div></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# LEFT COLUMN — CANDIDATE LIST
# ============================================================

def render_candidate_list():
    candidates = st.session_state.candidates
    query = st.session_state.search_query.lower()
    tab = st.session_state.status_tab

    filtered = [c for c in candidates if tab == "All" or c["status"] == tab]
    if query:
        filtered = [c for c in filtered if query in c["name"].lower() or query in c["role"].lower()
                    or any(query in s.lower() for s in c["skills"])]

    st.markdown(f"""
    <div class="panel-header">
        <div class="panel-title">Candidates <span class="count-badge">{len(filtered)}</span></div>
        <div class="no-photos">No Photos Mode</div>
    </div>
    """, unsafe_allow_html=True)

    tabs = ["All"] + STATUS_OPTIONS
    tab_cols = st.columns(len(tabs))
    for i, t in enumerate(tabs):
        with tab_cols[i]:
            btn_type = "primary" if st.session_state.status_tab == t else "secondary"
            if st.button(t, key=f"tab_{t}", use_container_width=True, type=btn_type):
                st.session_state.status_tab = t
                st.rerun()

    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

    if not filtered:
        if not candidates:
            st.markdown("""
            <div style="text-align:center; padding:40px 12px; color:#94a3b8;">
                <p style="font-weight:600; font-size:13px;">No candidates yet</p>
                <p style="font-size:11px;">Upload resumes to get started with AI-powered analysis.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding:40px 12px; color:#94a3b8;">
                <p style="font-weight:600; font-size:13px;">No candidates match filters</p>
                <p style="font-size:11px;">Try a different search or status tab.</p>
            </div>
            """, unsafe_allow_html=True)
        return

    for c in filtered:
        selected = c["id"] == st.session_state.selected_id
        with st.container(border=True):
            row = st.columns([1, 5, 3])
            with row[0]:
                cls = "initials-badge selected" if selected else "initials-badge"
                st.markdown(f'<div class="{cls}">{get_initials(c["name"])}</div>', unsafe_allow_html=True)
            with row[1]:
                st.markdown(f'<div style="font-weight:700; font-size:13px;">{c["name"]}</div>'
                             f'<div style="font-size:11px; color:#94a3b8;">{c["role"]}</div>', unsafe_allow_html=True)
            with row[2]:
                score_class = "score-high" if c["matchScore"] >= 90 else "score-mid"
                st.markdown(f'<span class="score-pill {score_class}">{c["matchScore"]}% AI</span>', unsafe_allow_html=True)

            st.markdown(f'<span class="pipeline-pill pill-{status_slug(c["status"])}">{c["status"]}</span>'
                         f'<span style="float:right; font-size:10px; color:#94a3b8;">{c["joinedDate"]}</span>',
                         unsafe_allow_html=True)

            if st.button("Select", key=f"select_{c['id']}", use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state.selected_id = c["id"]
                st.rerun()


# ============================================================
# MIDDLE COLUMN — CANDIDATE PROFILE
# ============================================================

def render_profile():
    c = find_candidate(st.session_state.selected_id)
    if not c:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#94a3b8;">
            <div style="font-size:15px; font-weight:700; margin-bottom:6px;">No candidate selected</div>
            <div style="font-size:12px;">Upload and analyze resumes to see candidate profiles here.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    header_cols = st.columns([3, 2])
    with header_cols[0]:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px;">
            <div class="initials-badge selected" style="width:48px; height:48px; border-radius:14px; font-size:15px;">{get_initials(c["name"])}</div>
            <div>
                <div style="font-size:16px; font-weight:800;">{c["name"]}</div>
                <div style="font-size:12px; color:#94a3b8;">{c["role"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with header_cols[1]:
        new_status = st.selectbox("Pipeline Stage", STATUS_OPTIONS,
                                   index=STATUS_OPTIONS.index(c["status"]), key=f"status_{c['id']}")
        if new_status != c["status"]:
            c["status"] = new_status
            st.rerun()

    st.markdown("<hr style='margin:14px 0; border-color:#f3f4f6;'>", unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Experience</div>'
                     f'<div class="metric-value">{c["experienceYears"]} Years</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">AI Match</div>'
                     f'<div class="metric-value accent">{c["matchScore"]}% Match</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    wf_col, dial_col = st.columns(2)
    with wf_col:
        st.markdown('<div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#475569; margin-bottom:8px;">Working Format</div>', unsafe_allow_html=True)
        wf = c["workingFormat"]
        for label, key, color in [("Remote", "remote", "#4f46e5"), ("Hybrid", "hybrid", "#10b981"), ("On-Site", "onsite", "#cbd5e1")]:
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">'
                         f'<span>{label}</span><span style="font-weight:700;">{wf[key]}%</span></div>', unsafe_allow_html=True)
        bar_html = '<div class="pref-bar-bg">'
        for key, color in [("remote", "#4f46e5"), ("hybrid", "#10b981"), ("onsite", "#cbd5e1")]:
            bar_html += f'<div class="pref-bar-fill" style="width:{wf[key]}%; background:{color};"></div>'
        bar_html += '</div>'
        st.markdown(bar_html, unsafe_allow_html=True)

    with dial_col:
        activity = c["metrics"]["weeklyActivity"]
        st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; background:var(--bg-section); border-radius:12px; padding:10px; height:100%;">
            <svg width="80" height="80" viewBox="0 0 36 36" style="transform:rotate(-90deg);">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="#e5e7eb" stroke-width="3.5" />
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="#4f46e5" stroke-width="3.5" stroke-linecap="round"
                      stroke-dasharray="{activity}, 100" />
            </svg>
            <div style="margin-top:-52px; text-align:center;">
                <div style="font-weight:800; font-size:14px;">{activity}%</div>
                <div style="font-size:7px; color:#94a3b8; font-family:{MONO_FONT};">ACTIVITY</div>
            </div>
            <div style="margin-top:34px; font-size:10px; color:#475569; width:100%;">
                {''.join(f'<div style="display:flex; justify-content:space-between; padding:0 6px;"><span>{s["label"]}</span><span style="font-weight:700;">{s["value"]}%</span></div>' for s in c["metrics"]["activitySplit"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px; font-weight:700; text-transform:uppercase; color:#475569; margin-bottom:10px;">{icon("briefcase", 14)} Career Trajectory History</div>', unsafe_allow_html=True)
    for job in c["history"]:
        st.markdown(f"""
        <div class="tl-item">
            <div class="tl-dot"></div>
            <div class="tl-meta"><span>{job["company"]}</span><span>{job["period"]}</span></div>
            <div class="tl-role">{job["role"]}</div>
            <div class="tl-desc">{job["description"]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:10px 0; border-color:#f3f4f6;'>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px; font-weight:700; text-transform:uppercase; color:#475569; margin-bottom:8px;">Assessed Technical Skillset</div>', unsafe_allow_html=True)
    st.markdown("".join(f'<span class="skill-tag">{s}</span>' for s in c["skills"]), unsafe_allow_html=True)

    st.markdown("<hr style='margin:14px 0; border-color:#f3f4f6;'>", unsafe_allow_html=True)
    sg_cols = st.columns(2)
    with sg_cols[0]:
        st.markdown(f'<div class="strengths-card"><div class="card-title g">{icon("thumbs-up", 12)} High-Fit Indicators</div>'
                     + "".join(f'<div style="font-size:11px; color:#475569; margin-bottom:4px;">• {s}</div>' for s in c["strengths"])
                     + '</div>', unsafe_allow_html=True)
    with sg_cols[1]:
        st.markdown(f'<div class="gaps-card"><div class="card-title r">{icon("thumbs-down", 12)} Potential Risk Gaps</div>'
                     + "".join(f'<div style="font-size:11px; color:#475569; margin-bottom:4px;">• {g}</div>' for g in c["gaps"])
                     + '</div>', unsafe_allow_html=True)


# ============================================================
# RIGHT COLUMN — AI CO-PILOT
# ============================================================

def get_ai_response(candidate: dict, question: str) -> str:
    if AI_AVAILABLE:
        try:
            q_lower = question.lower()
            jd_text = " ".join(candidate.get("skills", []))
            resume_text = candidate.get("role", "") + " " + " ".join(candidate.get("skills", []))
            skill_match = "Matching: " + ", ".join(candidate.get("skills", []))
            missing = ", ".join(candidate.get("gaps", []))

            if any(w in q_lower for w in ["interview", "question", "ask"]):
                chain = build_interview_questions_chain()
                return _invoke_with_retry(chain, {"jd_text": jd_text, "summary": resume_text})
            elif any(w in q_lower for w in ["score", "match", "rating", "fit"]):
                chain = build_score_chain()
                return _invoke_with_retry(chain, {"jd_text": jd_text, "skill_match": skill_match})
            elif any(w in q_lower for w in ["hire", "recommend", "decision", "hire"]):
                chain = build_hr_chain()
                score = str(candidate.get("matchScore", 50))
                return _invoke_with_retry(chain, {"score": score, "missing_skills": missing, "skill_match": skill_match})
            else:
                chain = build_summary_chain()
                return _invoke_with_retry(chain, {"resume_text": resume_text})
        except Exception as e:
            return f"AI analysis failed: {e}"
    return (f"AI pipeline not connected.\n\n"
            f"Based on {candidate['name']}'s profile ({candidate['matchScore']}% match):\n"
            f"Skills: {', '.join(candidate.get('skills', []))}\n"
            f"Gaps: {', '.join(candidate.get('gaps', []))}")


def render_ai_chat():
    c = find_candidate(st.session_state.selected_id)
    if not c:
        st.markdown("""
        <div class="ai-panel">
            <div style="text-align:center; padding:40px 20px; color:#94a3b8;">
                <div style="font-size:13px; font-weight:600;">AI Co-Recruiter</div>
                <div style="font-size:11px; margin-top:4px;">Select a candidate to start chatting.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    chat_key = c["id"]
    st.session_state.chats.setdefault(chat_key, [])

    st.markdown(f"""
    <div class="ai-panel">
        <div class="ai-header">
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:26px; height:26px; border-radius:8px; background:#6366f1; display:flex; align-items:center; justify-content:center;">{icon("sparkles", 14, "white")}</div>
                <div>
                    <div class="ai-title">AI Co-Recruiter</div>
                    <div class="ai-sub">Gemini 2.0 Flash · {c["name"]}</div>
                </div>
            </div>
            <span class="pulse-dot"></span>
        </div>
    """, unsafe_allow_html=True)

    history = st.session_state.chats[chat_key]
    if not history:
        st.markdown(f"""
        <div class="ai-empty">
            <p style="font-weight:700; color:#e2e8f0; font-size:12px;">Query Candidate Profile</p>
            <p>Ask about {c["name"]}'s qualifications or fit.</p>
        </div>
        """, unsafe_allow_html=True)
        preset_cols = st.columns(3)
        presets = [
            ("Technical Qs", f"Recommend 5 technical interview questions focused on: {', '.join(c['skills'])}."),
            ("Role Fit", "Evaluate strengths vs gaps and give a hire/no-hire confidence indicator."),
            ("Salary Audit", f"Review {c['targetSalary']} against {c['experienceYears']} years experience — reasonable?"),
        ]
        for col, (label, prompt) in zip(preset_cols, presets):
            with col:
                if st.button(label, key=f"preset_{label}_{c['id']}", use_container_width=True):
                    _run_ai_query(c, prompt)
                    st.rerun()
    else:
        for msg in history:
            css = "ai-msg-user" if msg["sender"] == "user" else "ai-msg-ai"
            st.markdown(f'<div class="{css}" style="margin-bottom:8px;">{msg["text"]}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    input_cols = st.columns([5, 1])
    with input_cols[0]:
        question = st.text_input("Ask", key=f"chat_input_{c['id']}", label_visibility="collapsed",
                                  placeholder="Ask anything about candidate...")
    with input_cols[1]:
        if st.button("Send", key=f"send_{c['id']}", use_container_width=True) and question.strip():
            _run_ai_query(c, question)
            st.rerun()


def _run_ai_query(candidate: dict, question: str):
    chat_key = candidate["id"]
    ts = datetime.now().strftime("%H:%M")
    st.session_state.chats[chat_key].append({"sender": "user", "text": question, "ts": ts})
    answer = get_ai_response(candidate, question)
    st.session_state.chats[chat_key].append({"sender": "ai", "text": answer, "ts": ts})


# ============================================================
# RIGHT COLUMN — TODAY'S INTERVIEWS (agenda)
# ============================================================

def render_agenda():
    st.markdown(f"""
    <div class="agenda-card">
        <div class="agenda-header">
            <div class="agenda-title">{icon("calendar", 14)} Today's Interviews</div>
            <div class="agenda-date">{datetime.now().strftime("%b %d")}</div>
        </div>
    """, unsafe_allow_html=True)

    events = st.session_state.get("events", [])
    if events:
        for evt in events:
            st.markdown(f"""
            <div class="agenda-event">
                <div>
                    <span class="agenda-time">{evt["time"]}</span>
                    <span class="agenda-type {evt["type"]}">{evt["type"]}</span>
                    <div class="agenda-event-title">{evt["title"]}</div>
                    <div class="agenda-event-with">{evt["meetingWith"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:24px 0;color:#94a3b8;font-size:13px;">
            No upcoming interviews scheduled
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# ADD CANDIDATE MODAL
# ============================================================

@st.dialog("Add Candidate Profile")
def add_candidate_dialog():
    with st.form("add_candidate_form"):
        name = st.text_input("Full Name *", placeholder="e.g. Rachel Adams")
        role = st.text_input("Professional Title *", placeholder="e.g. Senior Software Engineer")
        email = st.text_input("Email Address *", placeholder="e.g. rachel@example.com")
        skills = st.text_input("Technical Skills (comma separated) *", placeholder="e.g. React, TypeScript, AWS")

        c1, c2 = st.columns(2)
        with c1:
            experience_years = st.number_input("Experience (Years)", min_value=0, value=5)
        with c2:
            target_salary = st.text_input("Target Salary", value="$6,500")

        c3, c4 = st.columns(2)
        with c3:
            notice_period = st.text_input("Notice Period", value="Immediate")
        with c4:
            status = st.selectbox("Initial Status", ["Sourced", "In Progress", "Interview"])

        submitted = st.form_submit_button("Save Candidate", use_container_width=True, type="primary")
        if submitted:
            if not (name and role and email):
                st.error("Name, title, and email are required.")
                return
            skills_list = [s.strip() for s in skills.split(",") if s.strip()]
            new_id = f"cand-{int(datetime.now().timestamp())}"
            new_candidate = {
                "id": new_id, "name": name, "role": role, "email": email,
                "joinedDate": datetime.now().strftime("%b %d, %Y"), "status": status,
                "matchScore": 80, "experienceYears": experience_years,
                "targetSalary": target_salary, "noticePeriod": notice_period,
                "skills": skills_list or ["Not specified"],
                "metrics": {"weeklyActivity": 70, "activitySplit": [{"label": "Engineering", "value": 70}, {"label": "Sync & Planning", "value": 30}]},
                "workingFormat": {"remote": 70, "hybrid": 30, "onsite": 0},
                "history": [{"role": role, "company": "Previous Company", "period": "2023 - 2026", "description": "Full lifecycle development and technical execution."}],
                "strengths": [f"Strong proficiency in {skills_list[0] if skills_list else 'core role criteria'}."],
                "gaps": ["Needs further evaluation during interview stage."],
            }
            st.session_state.candidates.insert(0, new_candidate)
            st.session_state.selected_id = new_id
            st.rerun()


# ============================================================
# AI ANALYSIS PIPELINE
# ============================================================

def analyze_resume(resume_name: str, resume_text: str, jd_text: str):
    if not AI_AVAILABLE or build_candidate_result is None:
        return {"candidate_name": resume_name, "recommendation": "Error", "justification": "AI pipeline not available."}
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
        result = build_candidate_result(candidate_name=resume_name, summary_text=summary, skill_match_text=skill_match, score_text=score_text, hr_text=hr_text, interview_text=interview_text)
        return result.model_dump()
    except Exception as e:
        return {"candidate_name": resume_name, "recommendation": "Error", "justification": f"Analysis failed: {e}"}


def persist_results(jd_text: str, results: list[dict], resume_map: dict[str, str]):
    try:
        from ai.db import insert_job_description, insert_candidate_result
        jd_row = insert_job_description(title="Uploaded JD", raw_text=jd_text)
        jd_id = jd_row.get("id", "")
        for r in results:
            insert_candidate_result(
                jd_id=jd_id, candidate_name=r.get("candidate_name", ""), resume_text=resume_map.get(r.get("candidate_name", ""), ""),
                summary=r.get("summary", ""), education=r.get("education", ""),
                experience_years=r.get("experience_years", 0),
                matching_skills=r.get("matching_skills", []), missing_skills=r.get("missing_skills", []),
                extra_skills=r.get("extra_skills", []), score=r.get("score", 0),
                recommendation=r.get("recommendation", ""), justification=r.get("justification", ""),
                technical_questions=r.get("technical_questions", []), hr_questions=r.get("hr_questions", []),
                status="Sourced", email="",
            )
        return True
    except Exception:
        return False


def load_candidates_from_db() -> list[dict]:
    try:
        from ai.db import fetch_history
        rows = fetch_history(limit=200)
        if not rows:
            return []
        candidates = []
        for r in rows:
            c = {
                "id": r.get("id", ""),
                "name": r.get("candidate_name", "Unknown"),
                "role": r.get("education", "Not specified"),
                "email": r.get("email", ""),
                "joinedDate": (r.get("created_at", "") or "")[:10],
                "status": r.get("status", "Sourced"),
                "matchScore": r.get("score", 0),
                "experienceYears": r.get("experience_years", 0),
                "targetSalary": "Not specified",
                "noticePeriod": "Not specified",
                "skills": r.get("matching_skills", []) or [],
                "metrics": {"weeklyActivity": min(r.get("score", 50), 100), "activitySplit": [{"label": "Technical", "value": 70}, {"label": "Communication", "value": 30}]},
                "workingFormat": {"remote": 60, "hybrid": 30, "onsite": 10},
                "history": [{"role": r.get("education", "Professional"), "company": "Previous Role", "period": "Career", "description": (r.get("summary", "") or "")[:200]}],
                "strengths": (r.get("matching_skills", []) or [])[:5] or ["Strong technical profile."],
                "gaps": (r.get("missing_skills", []) or [])[:5] or ["Needs further evaluation."],
            }
            candidates.append(c)
        return candidates
    except Exception:
        return []


# ============================================================
# UPLOAD PAGE
# ============================================================

def render_upload_page():
    st.markdown("""
    <div class="upload-hero">
        <div class="upload-hero-icon">
    """ + icon("upload", 28, "white") + """
        </div>
        <h2>Upload Documents</h2>
        <p>Upload a Job Description and candidate Resumes (PDFs) to begin AI-powered analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    col_jd, col_cv = st.columns(2)

    with col_jd:
        st.markdown(f"""
        <div class="upload-section-title">{icon("file-text", 14)} Job Description</div>
        """, unsafe_allow_html=True)

        jd_file = st.file_uploader("Upload JD", type=["pdf"], key="upload_jd", label_visibility="collapsed")
        jd_text = ""

        if jd_file:
            if not jd_file.name.lower().endswith(".pdf"):
                st.error("Only PDF files are accepted.")
            elif jd_file.size > 10 * 1024 * 1024:
                st.error("File exceeds 10 MB limit.")
            elif PDF_AVAILABLE:
                jd_file.seek(0)
                result = pdf_extract(jd_file)
                if result.success:
                    jd_text = result.text
                    st.success(f"Extracted — {result.page_count} page{'s' if result.page_count != 1 else ''}")
                    with st.expander("Preview JD text"):
                        st.text_area("JD Preview", jd_text, height=160, disabled=True, key="jd_preview")
                else:
                    st.warning(result.warning or "Could not extract text.")
            else:
                st.warning("PDF reader not available.")

        st.markdown(f"""
        <div class="upload-section-title" style="margin-top:24px;">{icon("users", 14)} Candidate Resumes</div>
        """, unsafe_allow_html=True)

        cv_files = st.file_uploader("Upload Resumes", type=["pdf"], accept_multiple_files=True, key="upload_cvs", label_visibility="collapsed")

        resume_texts: list[tuple[str, str]] = []
        skipped: list[str] = []

        if cv_files:
            for f in cv_files:
                if not f.name.lower().endswith(".pdf"):
                    skipped.append(f"{f.name}: not a PDF")
                    continue
                if f.size > 10 * 1024 * 1024:
                    skipped.append(f"{f.name}: exceeds 10 MB")
                    continue
                if PDF_AVAILABLE:
                    f.seek(0)
                    result = pdf_extract(f)
                    if result.success:
                        resume_texts.append((f.name, result.text))
                    else:
                        skipped.append(f"{f.name}: {result.warning or 'extraction failed'}")
                else:
                    skipped.append(f"{f.name}: PDF reader not available")

            if resume_texts:
                st.success(f"{len(resume_texts)} resume{'s' if len(resume_texts) != 1 else ''} ready")
            if skipped:
                with st.expander(f"Skipped ({len(skipped)})"):
                    for msg in skipped:
                        st.warning(msg)

    with col_cv:
        if resume_texts or jd_text:
            st.markdown(f"""
            <div class="upload-section-title">{icon("target", 14)} Ready to Analyze</div>
            """, unsafe_allow_html=True)

            if jd_text:
                st.markdown(f"""
                <div class="upload-file-row">
                    <span style="color:var(--indigo-600);">{icon("file-text", 16)}</span>
                    <span class="upload-file-name">Job Description</span>
                    <span class="upload-file-size">{len(jd_text)} chars</span>
                </div>
                """, unsafe_allow_html=True)

            for name, text in resume_texts:
                st.markdown(f"""
                <div class="upload-file-row">
                    <span style="color:var(--emerald-500);">{icon("user", 16)}</span>
                    <span class="upload-file-name">{name}</span>
                    <span class="upload-file-size">{len(text)} chars</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            if st.button(f"Analyze {len(resume_texts)} Candidate{'s' if len(resume_texts) != 1 else ''}", type="primary", use_container_width=True):
                if not jd_text:
                    st.error("Please upload a Job Description first.")
                elif not resume_texts:
                    st.error("Please upload at least one Resume.")
                else:
                    resume_map = {name: text for name, text in resume_texts}
                    results = []
                    progress = st.progress(0.0, text="Starting analysis...")
                    status_box = st.empty()
                    for idx, (name, text) in enumerate(resume_texts):
                        status_box.info(f"Analyzing **{name}** ({idx + 1}/{len(resume_texts)})...")
                        result = analyze_resume(name, text, jd_text)
                        results.append(result)
                        progress.progress((idx + 1) / len(resume_texts), text=f"Completed {idx + 1}/{len(resume_texts)}")
                    status_box.success(f"Analysis complete — {len(results)} candidates processed.")

                    # Merge into session state
                    for r in results:
                        new_cand = {
                            "id": r.get("candidate_name", f"cand-{len(st.session_state.candidates)}"),
                            "name": r.get("candidate_name", "Unknown"),
                            "role": r.get("education", "Not specified"),
                            "email": "",
                            "joinedDate": datetime.now().strftime("%b %d, %Y"),
                            "status": "Sourced",
                            "matchScore": r.get("score", 0),
                            "experienceYears": r.get("experience_years", 0),
                            "targetSalary": "Not specified",
                            "noticePeriod": "Not specified",
                            "skills": r.get("matching_skills", []) or [],
                            "metrics": {"weeklyActivity": min(r.get("score", 50), 100), "activitySplit": [{"label": "Technical", "value": 70}, {"label": "Communication", "value": 30}]},
                            "workingFormat": {"remote": 60, "hybrid": 30, "onsite": 10},
                            "history": [{"role": r.get("education", "Professional"), "company": "Previous Role", "period": "Career", "description": (r.get("summary", "") or "")[:200]}],
                            "strengths": (r.get("matching_skills", []) or [])[:5] or ["Strong technical profile."],
                            "gaps": (r.get("missing_skills", []) or [])[:5] or ["Needs further evaluation."],
                        }
                        st.session_state.candidates.insert(0, new_cand)

                    # Persist to Supabase
                    persist_results(jd_text, results, resume_map)

                    st.session_state.selected_id = st.session_state.candidates[0]["id"]
                    st.session_state.page = "dashboard"
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                        padding:60px 20px;color:#94a3b8;text-align:center;">
                <div style="margin-bottom:12px;">{icon("upload", 32, "#cbd5e1")}</div>
                <p style="font-size:13px;font-weight:600;color:#64748b;margin:0;">No documents uploaded yet</p>
                <p style="font-size:11px;color:#94a3b8;margin:4px 0 0;">Upload a JD and Resumes on the left to get started.</p>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================

def render_footer():
    st.markdown(f"""
    <div class="talent-footer">
        <div>
            <div style="color:#e2e8f0; font-weight:700; font-size:11px;">TalentAI HR Dashboard Engine © 2026</div>
            <div style="font-size:10px; color:#475569; margin-top:2px;">Configured for syedrabiaan@gmail.com</div>
        </div>
        <div style="display:flex; gap:16px; align-items:center;">
            <span><span class="pulse-dot"></span> Server Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================

def main():
    st.set_page_config(page_title="TalentAI", layout="wide")
    inject_global_css()

    for key, default in [
        ("candidates", []),
        ("selected_id", ""),
        ("status_tab", "All"),
        ("search_query", ""),
        ("chats", {}),
        ("page", "dashboard"),
        ("db_loaded", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Load from DB on first run
    if not st.session_state.db_loaded:
        db_candidates = load_candidates_from_db()
        if db_candidates:
            st.session_state.candidates = db_candidates
            if not st.session_state.selected_id and db_candidates:
                st.session_state.selected_id = db_candidates[0]["id"]
        elif not st.session_state.candidates:
            st.session_state.candidates = []
        st.session_state.db_loaded = True

    if not st.session_state.selected_id and st.session_state.candidates:
        st.session_state.selected_id = st.session_state.candidates[0]["id"]

    render_header()

    page = st.session_state.page

    if page == "upload":
        render_upload_page()
    else:
        render_stats()
        col_list, col_profile, col_right = st.columns([4, 5, 3])
        with col_list:
            render_candidate_list()
        with col_profile:
            if st.session_state.candidates:
                render_profile()
        with col_right:
            if st.session_state.candidates:
                render_ai_chat()
                st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
                render_agenda()

    render_footer()


if __name__ == "__main__":
    main()
