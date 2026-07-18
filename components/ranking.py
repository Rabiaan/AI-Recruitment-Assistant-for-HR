from __future__ import annotations
import math
import streamlit as st

NOT_FOUND = "Not Found"
STATUS_TABS = ["All", "Sourced", "In Progress", "Interview", "Hired"]
BADGE_COLORS = ["#4f46e5", "#7c3aed", "#2563eb", "#0891b2", "#059669", "#d97706", "#dc2626", "#c026d3", "#0d9488", "#6366f1"]
MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"


def _badge_color(name: str) -> str:
    return BADGE_COLORS[sum(ord(c) for c in name) % len(BADGE_COLORS)]


def _initials(name: str) -> str:
    parts = name.strip().split()
    return (parts[0][0] + parts[1][0]).upper() if len(parts) >= 2 else name[:2].upper() if name else "?"


def _score_cls(score: int) -> str:
    return "score-high" if score >= 85 else "score-mid" if score >= 65 else "score-low"


def _pill_cls(status: str) -> str:
    return {"Sourced": "pill-sourced", "In Progress": "pill-in-progress", "Interview": "pill-interview", "Hired": "pill-hired"}.get(status, "pill-sourced")


def _rec_to_status(rec: str, cur: str) -> str:
    if cur and cur != "Sourced":
        return cur
    return {"Hire": "Hired", "Interview": "In Progress", "Reject": "Sourced"}.get(rec, "Sourced")


def _build_trajectory(cand: dict) -> list[dict]:
    items = []
    edu = cand.get("education", "") or ""
    if edu and edu != NOT_FOUND:
        items.append({"company": edu, "period": "Education", "role": "Academic Background", "desc": edu, "color": "#0891b2"})
    exp = cand.get("experience_years", 0) or 0
    summary = cand.get("summary", "") or ""
    if exp > 0:
        items.append({"company": "Professional Experience", "period": f"{exp}+ years", "role": "Career Overview", "desc": summary[:250] + "..." if len(summary) > 250 else summary, "color": "#4f46e5"})
    matching = cand.get("matching_skills", []) or []
    if matching:
        items.append({"company": "Core Competencies", "period": "Current", "role": "Technical Skills", "desc": ", ".join(matching), "color": "#059669"})
    extra = cand.get("extra_skills", []) or []
    if extra:
        items.append({"company": "Additional Skills", "period": "Peripheral", "role": "Cross-functional", "desc": ", ".join(extra[:8]), "color": "#d97706"})
    return items


def _derive_preferences(cand: dict) -> dict:
    combined = ((cand.get("summary", "") or "") + " " + " ".join(cand.get("matching_skills", []) or [])).lower()
    r = sum(2 for k in ["remote", "distributed", "freelance", "global", "async"] if k in combined) + 3
    h = sum(2 for k in ["hybrid", "flexible", "onsite", "office"] if k in combined) + 2
    o = sum(2 for k in ["onsite", "on-site", "in-office", "campus"] if k in combined) + 1
    t = r + h + o or 1
    return {"remote": round(r / t * 100), "hybrid": round(h / t * 100), "onsite": round(o / t * 100)}


def _derive_activity(cand: dict) -> list[dict]:
    skills = cand.get("matching_skills", []) or []
    if not skills:
        return [{"label": "General", "pct": 100}]
    cats = [
        ("Technical Research", ["python", "java", "sql", "aws", "docker", "kubernetes", "api", "backend", "frontend", "react", "node", "typescript"]),
        ("Design & UX", ["figma", "design", "ux", "ui", "css", "html", "photoshop", "sketch"]),
        ("Data Analysis", ["data", "analytics", "machine learning", "ml", "ai", "tensorflow", "pandas"]),
        ("Communication", ["agile", "scrum", "jira", "leadership", "team", "management"]),
    ]
    matched = []
    sl = " ".join(skills).lower()
    for label, kws in cats:
        c = sum(1 for k in kws if k in sl)
        if c > 0:
            matched.append((label, c))
    if not matched:
        matched = [("Technical Work", 3), ("Collaboration", 1)]
    total = sum(c for _, c in matched)
    return [{"label": l, "pct": round(c / total * 100)} for l, c in matched[:4]]


def _radial_svg(pct: int, color: str = "#4f46e5") -> str:
    r = 36
    circ = 2 * math.pi * r
    off = circ * (1 - pct / 100)
    return f'''<svg width="90" height="90" viewBox="0 0 90 90" style="transform:rotate(-90deg);">
        <circle cx="45" cy="45" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="7"/>
        <circle cx="45" cy="45" r="{r}" fill="none" stroke="{color}" stroke-width="7"
            stroke-dasharray="{circ}" stroke-dashoffset="{off}" stroke-linecap="round"/>
        <text x="45" y="45" text-anchor="middle" dominant-baseline="central" font-size="16" font-weight="800" fill="{color}"
            font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif" style="transform:rotate(90deg);transform-origin:center;">{pct}%</text>
    </svg>'''


# ===== LEFT COLUMN =====
def render_candidate_list(filtered: list[dict], all_candidates: list[dict]):
    st.markdown(f'<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="section-label">Candidates</p>', unsafe_allow_html=True)

    tabs_html = '<div class="pipeline-tabs">'
    for t in STATUS_TABS:
        act = "active" if st.session_state.status_tab == t else ""
        tabs_html += f'<div class="pipeline-tab {act}">{t}</div>'
    tabs_html += "</div>"
    st.markdown(tabs_html, unsafe_allow_html=True)

    tab_cols = st.columns(5)
    for i, t in enumerate(STATUS_TABS):
        with tab_cols[i]:
            if st.button(t, key=f"tab_{t}", use_container_width=True):
                st.session_state.status_tab = t
                st.session_state.selected_idx = 0
                st.rerun()

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin:12px 0 8px;">
        <span style="font-weight:600;font-size:13px;color:#0f172a;">All Candidates</span>
        <span style="background:#f3f4f6;color:#64748b;font-size:11px;padding:2px 10px;border-radius:9999px;font-weight:500;">{len(filtered)}</span>
    </div>
    """, unsafe_allow_html=True)

    if not filtered:
        st.markdown('<div class="empty-state" style="padding:32px 8px;"><p style="font-size:11px;color:#94a3b8;">No candidates match filters.</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    for idx, cand in enumerate(filtered):
        name = cand.get("candidate_name", "Unknown")
        score = cand.get("score", 0)
        status = cand.get("status", _rec_to_status(cand.get("recommendation", ""), ""))
        exp = cand.get("experience_years", 0) or 0
        edu = cand.get("education", NOT_FOUND) or NOT_FOUND
        badge = _badge_color(name)
        init = _initials(name)
        sel = "selected" if idx == st.session_state.selected_idx else ""

        st.markdown(f"""
        <div class="candidate-card {sel}">
            <div class="initials-badge" style="background:{badge};">{init}</div>
            <div style="flex:1;min-width:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
                    <span class="candidate-name">{name}</span>
                    <span class="score-pill {_score_cls(score)}">{score}% AI</span>
                </div>
                <div class="candidate-title">{edu}</div>
                <span class="pipeline-pill {_pill_cls(status)}">{status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Select {name}", key=f"sel_{idx}", use_container_width=True, label_visibility="collapsed"):
            st.session_state.selected_idx = idx
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ===== MIDDLE COLUMN =====
def render_candidate_profile(cand: dict):
    name = cand.get("candidate_name", "Unknown")
    score = cand.get("score", 0)
    status = cand.get("status", _rec_to_status(cand.get("recommendation", ""), ""))
    badge = _badge_color(name)
    init = _initials(name)
    edu = cand.get("education", NOT_FOUND) or NOT_FOUND
    exp = cand.get("experience_years", 0) or 0

    status_opts = ["Sourced", "In Progress", "Interview", "Hired"]
    cur_idx = status_opts.index(status) if status in status_opts else 0

    st.markdown(f"""
    <div class="profile-header">
        <div style="display:flex;align-items:center;gap:14px;">
            <div class="profile-avatar-lg" style="background:{badge};">{init}</div>
            <div>
                <div style="font-weight:700;font-size:17px;color:#0f172a;">{name}</div>
                <div style="font-size:11px;color:#64748b;margin-top:2px;">{edu}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    new_status = st.selectbox("Pipeline Stage", status_opts, index=cur_idx, key="pf_status", label_visibility="collapsed")
    if new_status != status:
        try:
            from ai.db import update_candidate_status
            cid = cand.get("id")
            if cid:
                update_candidate_status(cid, new_status)
        except Exception:
            pass
        cand["status"] = new_status
        st.rerun()

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0;">
        <div class="metric-card">
            <div class="metric-label">Experience</div>
            <div class="metric-value">{exp} Years</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">AI Match</div>
            <div class="metric-value" style="color:{badge};">{score}% Match</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    prefs = _derive_preferences(cand)
    activities = _derive_activity(cand)
    gauge_pct = min(sum(a["pct"] for a in activities), 100) or 75

    act_colors = ["#4f46e5", "#7c3aed", "#0891b2", "#d97706"]
    act_legend = ""
    for i, a in enumerate(activities):
        c = act_colors[i % len(act_colors)]
        act_legend += f'<div class="pref-legend-item"><span class="pref-dot" style="background:{c};"></span>{a["label"]}: {a["pct"]}%</div>'

    bar_colors = ["#3b82f6", "#8b5cf6", "#f59e0b"]
    bar_labels = ["Remote", "Hybrid", "On-Site"]
    bar_vals = [prefs["remote"], prefs["hybrid"], prefs["onsite"]]
    bar_segs = ""
    bar_legend = ""
    for lbl, val, clr in zip(bar_labels, bar_vals, bar_colors):
        bar_segs += f'<div class="pref-bar-fill" style="width:{val}%;background:{clr};"></div>'
        bar_legend += f'<div class="pref-legend-item"><span class="pref-dot" style="background:{clr};"></span>{lbl} {val}%</div>'

    st.markdown(f"""
    <div class="section-card">
        <div class="section-label" style="margin-bottom:12px;">Working Format</div>
        <div style="display:grid;grid-template-columns:1.2fr 0.8fr;gap:20px;align-items:center;">
            <div>
                <div style="font-size:11px;color:#64748b;margin-bottom:4px;">Work Style Distribution</div>
                <div class="pref-bar-bg">{bar_segs}</div>
                <div class="pref-legend">{bar_legend}</div>
            </div>
            <div style="text-align:center;">
                {_radial_svg(gauge_pct, badge)}
                <div style="font-size:10px;color:#94a3b8;margin-top:4px;font-family:{MONO_FONT};">ACTIVITY</div>
                <div class="pref-legend" style="justify-content:center;margin-top:6px;">{act_legend}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    summary = cand.get("summary", NOT_FOUND) or NOT_FOUND
    st.markdown(f"""
    <div class="section-card">
        <div class="section-label" style="margin-bottom:8px;">Summary</div>
        <p style="font-size:12px;color:#475569;line-height:1.7;margin:0;">{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    matching = cand.get("matching_skills", []) or []
    missing = cand.get("missing_skills", []) or []
    extra = cand.get("extra_skills", []) or []

    tags = ""
    for s in matching:
        tags += f'<span class="skill-tag tag-match">{s}</span>'
    for s in missing:
        tags += f'<span class="skill-tag tag-miss">{s}</span>'
    for s in extra:
        tags += f'<span class="skill-tag tag-extra">{s}</span>'
    if not tags:
        tags = f'<span style="font-size:11px;color:#94a3b8;">{NOT_FOUND}</span>'

    st.markdown(f"""
    <div class="section-card">
        <div class="section-label" style="margin-bottom:8px;">Assessed Technical Skillset</div>
        <div>{tags}</div>
    </div>
    """, unsafe_allow_html=True)

    s_items = "".join(f"<li style='margin-bottom:4px;'>{s}</li>" for s in matching[:6]) if matching else f"<li>{NOT_FOUND}</li>"
    g_items = "".join(f"<li style='margin-bottom:4px;'>{s}</li>" for s in missing[:6]) if missing else f"<li>{NOT_FOUND}</li>"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="strengths-card">
            <div class="card-title" style="color:#059669;">High-Fit Indicators</div>
            <ul style="font-size:11px;color:#475569;padding-left:16px;margin:0;line-height:1.6;">{s_items}</ul>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="gaps-card">
            <div class="card-title" style="color:#dc2626;">Potential Risk Gaps</div>
            <ul style="font-size:11px;color:#475569;padding-left:16px;margin:0;line-height:1.6;">{g_items}</ul>
        </div>
        """, unsafe_allow_html=True)

    trajectory = _build_trajectory(cand)
    if trajectory:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="margin-bottom:12px;">Career Trajectory History</div>', unsafe_allow_html=True)
        tl = '<div style="position:relative;padding-left:28px;">'
        for i, item in enumerate(trajectory):
            last = i == len(trajectory) - 1
            tl += f"""<div class="tl-item">
                <div class="tl-dot" style="border-color:{item['color']};"></div>
                {'<div class="tl-line"></div>' if not last else ''}
                <div class="tl-meta"><span>{item['company']}</span><span>{item['period']}</span></div>
                <div class="tl-role">{item['role']}</div>
                <div class="tl-desc">{item['desc']}</div>
            </div>"""
        tl += '</div>'
        st.markdown(tl, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    justification = cand.get("justification", NOT_FOUND) or NOT_FOUND
    st.markdown(f"""
    <div class="section-card" style="background:#eff6ff;border-color:#bfdbfe;">
        <div class="section-label" style="margin-bottom:6px;">AI Justification</div>
        <p style="font-size:12px;color:#475569;margin:0;line-height:1.6;">{justification}</p>
    </div>
    """, unsafe_allow_html=True)

    tech_qs = cand.get("technical_questions", []) or []
    hr_qs = cand.get("hr_questions", []) or []
    if tech_qs or hr_qs:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="margin-bottom:8px;">Suggested Interview Questions</div>', unsafe_allow_html=True)
        q1, q2 = st.columns(2)
        with q1:
            if tech_qs:
                st.markdown("**Technical**")
                for i, q in enumerate(tech_qs, 1):
                    st.markdown(f"{i}. {q}")
        with q2:
            if hr_qs:
                st.markdown("**HR / Behavioral**")
                for i, q in enumerate(hr_qs, 1):
                    st.markdown(f"{i}. {q}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    ec, hc = st.columns(2)
    with ec:
        if st.button("Export CSV", use_container_width=True):
            from utils.parser import CandidateResult
            from app import export_csv
            r = CandidateResult(**{k: v for k, v in cand.items() if k in CandidateResult.model_fields})
            csv_bytes, filename = export_csv([r])
            st.download_button("Download CSV", data=csv_bytes, file_name=filename, mime="text/csv", use_container_width=True)
    with hc:
        cid = cand.get("id")
        if cid:
            try:
                from ai.db import fetch_candidate_activities
                acts = fetch_candidate_activities(cid)
                if acts:
                    with st.expander(f"Activity Log ({len(acts)})"):
                        for a in acts:
                            st.caption(f"**{a.get('activity_type', '')}** — {a.get('description', '')}")
            except Exception:
                pass
