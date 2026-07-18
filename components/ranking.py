from __future__ import annotations
import streamlit as st
import math

NOT_FOUND = "Not Found"

STATUS_TABS = ["All", "Sourced", "In Progress", "Interview", "Hired"]

BADGE_COLORS = [
    "#4f46e5", "#7c3aed", "#2563eb", "#0891b2", "#059669",
    "#d97706", "#dc2626", "#c026d3", "#0d9488", "#6366f1",
]

MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"


def _get_badge_color(name: str) -> str:
    h = sum(ord(c) for c in name)
    return BADGE_COLORS[h % len(BADGE_COLORS)]


def _get_initials(name: str) -> str:
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


def _status_pill_class(status: str) -> str:
    return {
        "Sourced": "pill-sourced",
        "In Progress": "pill-in-progress",
        "Interview": "pill-interview",
        "Hired": "pill-hired",
    }.get(status, "pill-sourced")


def _rec_to_status(recommendation: str, current: str) -> str:
    if current and current != "Sourced":
        return current
    return {"Hire": "Hired", "Interview": "In Progress", "Reject": "Sourced"}.get(recommendation, "Sourced")


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
            "color": "#0891b2",
        })

    experience = cand.get("experience_years", 0)
    if experience > 0:
        items.append({
            "company": "Professional Experience",
            "period": f"{experience}+ years",
            "role": "Career Overview",
            "desc": summary[:200] + "..." if len(summary) > 200 else summary,
            "color": "#4f46e5",
        })

    matching = cand.get("matching_skills", []) or []
    if matching:
        items.append({
            "company": "Core Competencies",
            "period": "Current",
            "role": "Technical Skills",
            "desc": ", ".join(matching),
            "color": "#059669",
        })

    extra = cand.get("extra_skills", []) or []
    if extra:
        items.append({
            "company": "Additional Skills",
            "period": "Peripheral",
            "role": "Cross-functional Abilities",
            "desc": ", ".join(extra[:8]),
            "color": "#d97706",
        })

    return items


def _derive_preferences(cand: dict) -> dict:
    summary = (cand.get("summary", "") or "").lower()
    skills = " ".join(cand.get("matching_skills", []) or []).lower()
    combined = summary + " " + skills

    remote_kw = ["remote", "distributed", "freelance", "consultant", "global", "async"]
    hybrid_kw = ["hybrid", "flexible", "onsite", "office"]
    onsite_kw = ["onsite", "on-site", "in-office", "campus", "facility"]

    r = sum(2 for k in remote_kw if k in combined) + 3
    h = sum(2 for k in hybrid_kw if k in combined) + 2
    o = sum(2 for k in onsite_kw if k in combined) + 1
    total = r + h + o or 1
    return {"remote": round(r / total * 100), "hybrid": round(h / total * 100), "onsite": round(o / total * 100)}


def _derive_activity(cand: dict) -> list[dict]:
    skills = cand.get("matching_skills", []) or []
    if not skills:
        return [{"label": "General", "pct": 100}]

    categories = [
        ("Technical Research", ["python", "java", "sql", "aws", "docker", "kubernetes", "api", "backend", "frontend", "react", "node", "typescript"]),
        ("Design & UX", ["figma", "design", "ux", "ui", "css", "html", "photoshop", "sketch"]),
        ("Data Analysis", ["data", "analytics", "machine learning", "ml", "ai", "tensorflow", "pandas", "statistics"]),
        ("Communication", ["agile", "scrum", "jira", "leadership", "team", "management"]),
    ]

    matched = []
    skills_lower = " ".join(skills).lower()
    for label, keywords in categories:
        count = sum(1 for k in keywords if k in skills_lower)
        if count > 0:
            matched.append((label, count))

    if not matched:
        matched = [("Technical Work", 3), ("Collaboration", 1)]

    total = sum(c for _, c in matched)
    return [{"label": label, "pct": round(count / total * 100)} for label, count in matched[:4]]


def _radial_svg(percentage: int, color: str = "#4f46e5") -> str:
    r = 42
    circ = 2 * math.pi * r
    offset = circ * (1 - percentage / 100)
    return f'''
    <svg width="100" height="100" viewBox="0 0 100 100" style="transform: rotate(-90deg);">
        <circle cx="50" cy="50" r="{r}" fill="none" stroke="#e2e8f0" stroke-width="8"/>
        <circle cx="50" cy="50" r="{r}" fill="none" stroke="{color}" stroke-width="8"
            stroke-dasharray="{circ}" stroke-dashoffset="{offset}"
            stroke-linecap="round" style="transition: stroke-dashoffset 0.6s ease;"/>
        <text x="50" y="50" text-anchor="middle" dominant-baseline="central"
            font-size="18" font-weight="800" fill="{color}"
            font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            style="transform: rotate(90deg); transform-origin: center;">
            {percentage}%
        </text>
    </svg>'''


# ===========================
# LEFT COLUMN: Candidate List
# ===========================
def render_candidate_list(filtered: list[dict], all_candidates: list[dict]):
    st.markdown('<p class="section-label">&#128101; Candidates</p>', unsafe_allow_html=True)

    tab_html = '<div class="pipeline-tabs">'
    for tab in STATUS_TABS:
        active = "active" if st.session_state.status_tab == tab else ""
        tab_html += f'<div class="pipeline-tab {active}">{tab}</div>'
    tab_html += "</div>"
    st.markdown(tab_html, unsafe_allow_html=True)

    tab_cols = st.columns(5)
    for i, tab in enumerate(STATUS_TABS):
        with tab_cols[i]:
            if st.button(tab, key=f"tab_{tab}", use_container_width=True):
                st.session_state.status_tab = tab
                st.session_state.selected_idx = 0
                st.rerun()

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin:12px 0 8px;">
        <span style="font-weight:600;font-size:13px;color:#0f172a;">All Candidates</span>
        <span style="background:#f1f5f9;color:#64748b;font-size:11px;padding:2px 10px;border-radius:9999px;font-weight:500;">{len(filtered)}</span>
    </div>
    """, unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div class="empty-state" style="padding:48px 16px;">
            <p style="font-size:40px;margin:0;">&#128100;</p>
            <p style="font-weight:600;color:#64748b;margin:12px 0 0 0;">No candidates found</p>
            <p style="font-size:11px;color:#94a3b8;margin:4px 0 0 0;">Try adjusting filters or search terms.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    for idx, cand in enumerate(filtered):
        name = cand.get("candidate_name", "Unknown")
        score = cand.get("score", 0)
        status = cand.get("status", _rec_to_status(cand.get("recommendation", ""), ""))
        education = cand.get("education", NOT_FOUND) or NOT_FOUND
        experience = cand.get("experience_years", 0) or 0
        date_str = cand.get("created_at", "")
        if date_str:
            try:
                date_str = date_str[:10]
            except Exception:
                date_str = ""

        initials = _get_initials(name)
        badge_color = _get_badge_color(name)
        is_selected = idx == st.session_state.selected_idx
        card_cls = "selected" if is_selected else ""
        score_cls = _score_class(score)
        pill_cls = _status_pill_class(status)
        title = f"{experience}+ yrs exp" if experience else education

        card_html = f"""
        <div class="candidate-card {card_cls}">
            <div class="initials-badge" style="background:{badge_color};">{initials}</div>
            <div style="flex:1;min-width:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
                    <span class="candidate-name">{name}</span>
                    <span class="score-pill {score_cls}">{score}% AI</span>
                </div>
                <div class="candidate-title">{title}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;gap:4px;">
                    <span class="pipeline-pill {pill_cls}">{status}</span>
                    {'<span class="candidate-date">' + date_str + "</span>" if date_str else ""}
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        if st.button(f"Select {name}", key=f"sel_{idx}", use_container_width=True, label_visibility="collapsed"):
            st.session_state.selected_idx = idx
            st.rerun()


# ===========================
# MIDDLE COLUMN: Full Profile
# ===========================
def render_candidate_profile(cand: dict):
    name = cand.get("candidate_name", "Unknown")
    score = cand.get("score", 0)
    status = cand.get("status", _rec_to_status(cand.get("recommendation", ""), ""))
    initials = _get_initials(name)
    badge_color = _get_badge_color(name)
    score_cls = _score_class(score)

    status_options = ["Sourced", "In Progress", "Interview", "Hired"]
    current_idx = status_options.index(status) if status in status_options else 0
    education = cand.get("education", NOT_FOUND) or NOT_FOUND
    experience = cand.get("experience_years", 0) or 0
    recommendation = cand.get("recommendation", NOT_FOUND) or NOT_FOUND

    # Profile Header
    st.markdown(f"""
    <div class="profile-header" style="padding:16px 20px;">
        <div style="display:flex;align-items:center;gap:14px;">
            <div class="profile-avatar-lg" style="background:{badge_color};">{initials}</div>
            <div>
                <div style="font-weight:700;font-size:17px;color:#0f172a;">{name}</div>
                <div style="font-size:11px;color:#64748b;margin-top:2px;">{education}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    new_status = st.selectbox(
        "Pipeline Stage", status_options, index=current_idx,
        key="profile_status_select", label_visibility="collapsed",
    )
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
            st.rerun()

    # Key Metrics Grid
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0;">
        <div class="metric-card">
            <div class="metric-label">Total Experience</div>
            <div class="metric-value">{experience} Years</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">AI Match Score</div>
            <div class="metric-value" style="color:{badge_color};">{score}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Working Format & Preferences
    prefs = _derive_preferences(cand)
    activities = _derive_activity(cand)
    total_activity = sum(a["pct"] for a in activities)
    if total_activity > 0:
        gauge_pct = min(total_activity, 100)
    else:
        gauge_pct = 75

    activity_colors = ["#4f46e5", "#7c3aed", "#0891b2", "#d97706"]
    legend_html = ""
    for i, a in enumerate(activities):
        c = activity_colors[i % len(activity_colors)]
        legend_html += f'<div class="pref-legend-item"><span class="pref-dot" style="background:{c};"></span>{a["label"]}: {a["pct"]}%</div>'

    bar_segments = ""
    bar_colors = ["#3b82f6", "#8b5cf6", "#f59e0b"]
    bar_labels = ["Remote", "Hybrid", "On-site"]
    bar_values = [prefs["remote"], prefs["hybrid"], prefs["onsite"]]
    legend_parts = ""
    for i, (lbl, val, clr) in enumerate(zip(bar_labels, bar_values, bar_colors)):
        bar_segments += f'<div class="pref-bar-fill" style="width:{val}%;background:{clr};"></div>'
        legend_parts += f'<div class="pref-legend-item"><span class="pref-dot" style="background:{clr};"></span>{lbl} {val}%</div>'

    gauge_svg = _radial_svg(gauge_pct, badge_color)

    st.markdown(f"""
    <div style="padding:16px 20px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;margin-bottom:16px;">
        <div class="section-label" style="margin-bottom:12px;">Working Format & Preferences</div>
        <div style="display:grid;grid-template-columns:1.2fr 0.8fr;gap:20px;align-items:center;">
            <div>
                <div style="font-size:11px;color:#64748b;margin-bottom:4px;">Work Style Distribution</div>
                <div class="pref-bar-bg">{bar_segments}</div>
                <div class="pref-legend">{legend_parts}</div>
            </div>
            <div class="gauge-container">
                {gauge_svg}
                <div class="gauge-label">Weekly Activity Output</div>
                <div class="pref-legend" style="justify-content:center;margin-top:8px;">{legend_html}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Summary
    summary = cand.get("summary", NOT_FOUND) or NOT_FOUND
    st.markdown(f"""
    <div style="padding:16px 20px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;margin-bottom:16px;">
        <div class="section-label" style="margin-bottom:8px;">&#128196; Summary</div>
        <p style="font-size:12px;color:#475569;line-height:1.7;margin:0;">{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # Assessed Technical Skillset
    matching = cand.get("matching_skills", []) or []
    missing = cand.get("missing_skills", []) or []
    extra = cand.get("extra_skills", []) or []

    st.markdown('<div class="section-label" style="margin-bottom:8px;">&#128736; Assessed Technical Skillset</div>', unsafe_allow_html=True)
    tags_html = ""
    for s in matching:
        tags_html += f'<span class="skill-tag tag-match">{s}</span>'
    for s in missing:
        tags_html += f'<span class="skill-tag tag-miss">{s}</span>'
    for s in extra:
        tags_html += f'<span class="skill-tag tag-extra">{s}</span>'
    if not tags_html:
        tags_html = f'<span style="font-size:11px;color:#94a3b8;">{NOT_FOUND}</span>'
    st.markdown(f'<div style="margin-bottom:16px;">{tags_html}</div>', unsafe_allow_html=True)

    # Qualitative Fit Indicators
    s_col, g_col = st.columns(2)
    with s_col:
        strength_items = "".join([f"<li style='margin-bottom:4px;'>{s}</li>" for s in matching[:6]]) if matching else f"<li>{NOT_FOUND}</li>"
        st.markdown(f"""
        <div class="strengths-card">
            <div class="card-title" style="color:#059669;">&#128077; High-Fit Indicators</div>
            <ul style="font-size:11px;color:#475569;padding-left:16px;margin:0;line-height:1.6;">{strength_items}</ul>
        </div>
        """, unsafe_allow_html=True)

    with g_col:
        gap_items = "".join([f"<li style='margin-bottom:4px;'>{s}</li>" for s in missing[:6]]) if missing else f"<li>{NOT_FOUND}</li>"
        st.markdown(f"""
        <div class="gaps-card">
            <div class="card-title" style="color:#dc2626;">&#128078; Potential Risk Gaps</div>
            <ul style="font-size:11px;color:#475569;padding-left:16px;margin:0;line-height:1.6;">{gap_items}</ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Career Trajectory History
    trajectory = _build_trajectory(cand)
    if trajectory:
        st.markdown('<div class="section-label" style="margin-bottom:12px;">&#128188; Career Trajectory History</div>', unsafe_allow_html=True)
        tl_html = '<div style="position:relative;padding-left:28px;">'
        for i, item in enumerate(trajectory):
            is_last = i == len(trajectory) - 1
            tl_html += f"""
            <div class="tl-item">
                <div class="tl-dot" style="border-color:{item.get('color', '#4f46e5')};"></div>
                {'<div class="tl-line"></div>' if not is_last else ''}
                <div class="tl-meta"><span>{item['company']}</span><span>{item['period']}</span></div>
                <div class="tl-role">{item['role']}</div>
                <div class="tl-desc">{item['desc']}</div>
            </div>
            """
        tl_html += '</div>'
        st.markdown(tl_html, unsafe_allow_html=True)

    # Justification
    justification = cand.get("justification", NOT_FOUND) or NOT_FOUND
    st.markdown(f"""
    <div style="padding:14px 16px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;margin-top:12px;">
        <div class="section-label" style="margin-bottom:6px;">&#128172; AI Justification</div>
        <p style="font-size:12px;color:#475569;margin:0;line-height:1.6;">{justification}</p>
    </div>
    """, unsafe_allow_html=True)

    # Interview Questions
    tech_qs = cand.get("technical_questions", []) or []
    hr_qs = cand.get("hr_questions", []) or []
    if tech_qs or hr_qs:
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="margin-bottom:8px;">&#128172; Suggested Interview Questions</div>', unsafe_allow_html=True)
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
            st.download_button("Download CSV", data=csv_bytes, file_name=filename, mime="text/csv", use_container_width=True)

    with hist_col:
        cid = cand.get("id")
        if cid:
            try:
                from ai.db import fetch_candidate_activities
                activities_db = fetch_candidate_activities(cid)
                if activities_db:
                    with st.expander(f"Activity Log ({len(activities_db)})"):
                        for act in activities_db:
                            st.caption(f"**{act.get('activity_type', '')}** — {act.get('description', '')}")
            except Exception:
                pass
