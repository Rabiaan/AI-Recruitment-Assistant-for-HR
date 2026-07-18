import streamlit as st

NOT_FOUND = "Not Found"

STATUS_TABS = ["All", "Sourced", "In Progress", "Interview", "Hired"]


def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if name else "?"


def _score_class(score: int) -> str:
    if score >= 85:
        return "score-high"
    elif score >= 65:
        return "score-mid"
    return "score-low"


def _status_class(status: str) -> str:
    return {
        "Sourced": "status-sourced",
        "In Progress": "status-in-progress",
        "Interview": "status-interview",
        "Hired": "status-hired",
    }.get(status, "status-sourced")


def _rec_to_status(recommendation: str, current: str) -> str:
    if current and current != "Sourced":
        return current
    return {
        "Hire": "Hired",
        "Interview": "In Progress",
        "Reject": "Sourced",
    }.get(recommendation, "Sourced")


def render_candidate_list(filtered: list[dict], all_candidates: list[dict]):
    st.markdown(f'<p class="section-mono">&#128101; Candidates</p>', unsafe_allow_html=True)

    # Pipeline tabs
    tab_html = '<div class="pipeline-tabs">'
    for tab in STATUS_TABS:
        active = "active" if st.session_state.status_tab == tab else ""
        tab_html += f'<div class="pipeline-tab {active}" id="tab_{tab.replace(" ", "_")}">{tab}</div>'
    tab_html += "</div>"
    st.markdown(tab_html, unsafe_allow_html=True)

    # Actual tab buttons (invisible, on top of styled tabs)
    tab_cols = st.columns(5)
    for i, tab in enumerate(STATUS_TABS):
        with tab_cols[i]:
            if st.button(tab, key=f"tab_{tab}", use_container_width=True):
                st.session_state.status_tab = tab
                st.session_state.selected_idx = 0
                st.rerun()

    # Search
    search = st.text_input("Search", placeholder="Search by name, skill, or role...", label_visibility="collapsed", key="search_input")
    if search != st.session_state.get("search_query", ""):
        st.session_state.search_query = search
        st.session_state.selected_idx = 0
        st.rerun()

    # Count badge
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><span style="font-weight:600;font-size:13px;color:#1e293b;">Candidates</span><span style="background:#f1f5f9;color:#64748b;font-size:11px;padding:2px 8px;border-radius:9999px;">{len(filtered)}</span></div>', unsafe_allow_html=True)

    # Candidate cards
    if not filtered:
        st.markdown('<div class="empty-state" style="padding:40px 16px;"><p style="font-size:40px;margin:0;">&#128100;</p><p style="font-weight:500;color:#64748b;margin:8px 0 0 0;">No candidates match filters</p><p style="font-size:11px;color:#94a3b8;margin:4px 0 0 0;">Try a different search or tab.</p></div>', unsafe_allow_html=True)
        return

    for idx, cand in enumerate(filtered):
        name = cand.get("candidate_name", "Unknown")
        score = cand.get("score", 0)
        status = cand.get("status", _rec_to_status(cand.get("recommendation", ""), ""))
        role_parts = []
        if cand.get("education") and cand["education"] != NOT_FOUND:
            role_parts.append(cand["education"])
        role_text = role_parts[0] if role_parts else NOT_FOUND
        initials = get_initials(name)
        is_selected = idx == st.session_state.selected_idx
        card_class = "selected" if is_selected else ""
        initials_class = "active" if is_selected else "default"
        score_cls = _score_class(score)
        status_cls = _status_class(status)

        card_html = f"""
        <div class="candidate-card {card_class}" id="card_{idx}">
            <div class="candidate-initials {initials_class}">{initials}</div>
            <div style="flex:1;min-width:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:4px;">
                    <span class="candidate-name">{name}</span>
                    <span class="score-badge {score_cls}">{score}% AI</span>
                </div>
                <div class="candidate-role">{role_text}</div>
                <div class="candidate-meta">
                    <span class="status-badge {status_cls}">{status}</span>
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        if st.button(f"Select {name}", key=f"sel_{idx}", use_container_width=True, label_visibility="collapsed"):
            st.session_state.selected_idx = idx
            st.rerun()


def render_candidate_profile(cand: dict):
    name = cand.get("candidate_name", "Unknown")
    score = cand.get("score", 0)
    status = cand.get("status", _rec_to_status(cand.get("recommendation", ""), ""))
    initials = get_initials(name)
    score_cls = _score_class(score)

    # Header
    status_options = ["Sourced", "In Progress", "Interview", "Hired"]
    current_status_idx = status_options.index(status) if status in status_options else 0

    st.markdown(f"""
    <div class="profile-header">
        <div style="display:flex;align-items:center;gap:12px;">
            <div class="profile-avatar-lg">{initials}</div>
            <div>
                <div style="font-weight:700;font-size:16px;color:#1e293b;">{name}</div>
                <div style="font-size:11px;color:#94a3b8;">{cand.get('education', NOT_FOUND)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Status changer
    new_status = st.selectbox("Pipeline Stage", status_options, index=current_status_idx, key="status_select", label_visibility="collapsed")
    if new_status != status:
        try:
            from ai.db import update_candidate_status
            cid = cand.get("id")
            if cid:
                update_candidate_status(cid, new_status)
                cand["status"] = new_status
                st.rerun()
        except Exception:
            cand["status"] = new_status

    # Metrics grid
    experience = cand.get("experience_years", 0) or 0
    education = cand.get("education", NOT_FOUND) or NOT_FOUND
    email = cand.get("email", NOT_FOUND) or NOT_FOUND

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0;">
        <div class="profile-metric">
            <div class="profile-metric-label">Experience</div>
            <div class="profile-metric-value">{experience} Years</div>
        </div>
        <div class="profile-metric">
            <div class="profile-metric-label">AI Match</div>
            <div class="profile-metric-value" style="color:#4f46e5;">{score}% Match</div>
        </div>
        <div class="profile-metric">
            <div class="profile-metric-label">Education</div>
            <div class="profile-metric-value" style="font-size:11px;">{education}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Summary
    summary = cand.get("summary", NOT_FOUND) or NOT_FOUND
    st.markdown(f"""
    <div style="padding:16px;background:#f8fafc;border-radius:12px;border:1px solid #f1f5f9;margin-bottom:16px;">
        <div class="section-mono" style="margin-bottom:8px;">&#128196; Summary</div>
        <p style="font-size:12px;color:#475569;line-height:1.6;margin:0;">{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # Skills
    matching = cand.get("matching_skills", []) or []
    missing = cand.get("missing_skills", []) or []
    extra = cand.get("extra_skills", []) or []

    st.markdown('<div class="section-mono" style="margin-bottom:8px;">&#128736; Assessed Technical Skillset</div>', unsafe_allow_html=True)
    pills = ""
    for s in matching:
        pills += f'<span class="skill-pill pill-match">{s}</span>'
    for s in missing:
        pills += f'<span class="skill-pill pill-miss">{s}</span>'
    for s in extra:
        pills += f'<span class="skill-pill pill-extra">{s}</span>'
    if not pills:
        pills = f'<span style="font-size:11px;color:#94a3b8;">{NOT_FOUND}</span>'
    st.markdown(f'<div style="margin-bottom:16px;">{pills}</div>', unsafe_allow_html=True)

    # Strengths & Gaps (two columns)
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
    """, unsafe_allow_html=True)

    s_col, g_col = st.columns(2)
    with s_col:
        strength_items = "".join([f"<li>{s}</li>" for s in matching[:5]]) if matching else f"<li>{NOT_FOUND}</li>"
        st.markdown(f"""
        <div class="strengths-box">
            <div class="box-title" style="color:#065f46;">&#128077; High-Fit Indicators</div>
            <ul style="font-size:11px;color:#475569;padding-left:16px;margin:0;">{strength_items}</ul>
        </div>
        """, unsafe_allow_html=True)

    with g_col:
        gap_items = "".join([f"<li>{s}</li>" for s in missing[:5]]) if missing else f"<li>{NOT_FOUND}</li>"
        st.markdown(f"""
        <div class="gaps-box">
            <div class="box-title" style="color:#991b1b;">&#128078; Potential Risk Gaps</div>
            <ul style="font-size:11px;color:#475569;padding-left:16px;margin:0;">{gap_items}</ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Career Trajectory
    trajectory = _build_trajectory(cand)
    if trajectory:
        st.markdown('<div class="section-mono" style="margin-bottom:12px;">&#128188; Career Trajectory History</div>', unsafe_allow_html=True)
        timeline_html = '<div style="position:relative;padding-left:24px;">'
        for i, item in enumerate(trajectory):
            is_last = i == len(trajectory) - 1
            timeline_html += f"""
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                {'<div class="timeline-line"></div>' if not is_last else ''}
                <div class="timeline-company"><span>{item['company']}</span><span>{item['period']}</span></div>
                <div class="timeline-role">{item['role']}</div>
                <div class="timeline-desc">{item['desc']}</div>
            </div>
            """
        timeline_html += '</div>'
        st.markdown(timeline_html, unsafe_allow_html=True)

    # Justification
    justification = cand.get("justification", NOT_FOUND) or NOT_FOUND
    st.markdown(f"""
    <div style="padding:12px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;margin-top:16px;">
        <div class="section-mono" style="margin-bottom:6px;">&#128172; Justification</div>
        <p style="font-size:12px;color:#475569;margin:0;line-height:1.5;">{justification}</p>
    </div>
    """, unsafe_allow_html=True)

    # Interview Questions
    tech_qs = cand.get("technical_questions", []) or []
    hr_qs = cand.get("hr_questions", []) or []
    if tech_qs or hr_qs:
        st.markdown("---")
        st.markdown('<div class="section-mono" style="margin-bottom:8px;">&#128172; Interview Questions</div>', unsafe_allow_html=True)
        q1, q2 = st.columns(2)
        with q1:
            if tech_qs:
                st.markdown("**Technical**")
                for i, q in enumerate(tech_qs, 1):
                    st.markdown(f"{i}. {q}")
            else:
                st.markdown(f"**Technical:** {NOT_FOUND}")
        with q2:
            if hr_qs:
                st.markdown("**HR / Behavioral**")
                for i, q in enumerate(hr_qs, 1):
                    st.markdown(f"{i}. {q}")
            else:
                st.markdown(f"**HR / Behavioral:** {NOT_FOUND}")

    # Export
    st.markdown("---")
    export_col, hist_col = st.columns(2)
    with export_col:
        if st.button("Export CSV", use_container_width=True):
            from utils.parser import CandidateResult
            from app import export_csv
            r = CandidateResult(**{k: v for k, v in cand.items() if k in CandidateResult.model_fields})
            csv_bytes, filename = export_csv([r])
            st.download_button("Download", data=csv_bytes, file_name=filename, mime="text/csv", use_container_width=True)

    with hist_col:
        cid = cand.get("id")
        if cid:
            try:
                from ai.db import fetch_candidate_activities
                activities = fetch_candidate_activities(cid)
                if activities:
                    with st.expander(f"Activity Log ({len(activities)})"):
                        for act in activities:
                            st.caption(f"**{act.get('activity_type', '')}** — {act.get('description', '')}")
            except Exception:
                pass


def _build_trajectory(cand: dict) -> list[dict]:
    items = []
    summary = cand.get("summary", "") or ""
    education = cand.get("education", "") or ""

    if education and education != NOT_FOUND:
        items.append({
            "company": education,
            "period": "Education",
            "role": "Academic Background",
            "desc": education,
        })

    experience = cand.get("experience_years", 0)
    if experience > 0:
        items.append({
            "company": "Professional Experience",
            "period": f"{experience}+ years",
            "role": "Career Overview",
            "desc": summary[:200] + "..." if len(summary) > 200 else summary,
        })

    matching = cand.get("matching_skills", []) or []
    if matching:
        items.append({
            "company": "Core Competencies",
            "period": "Current",
            "role": "Technical Skills",
            "desc": ", ".join(matching),
        })

    return items
