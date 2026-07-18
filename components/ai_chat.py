from __future__ import annotations
import streamlit as st
from ai.llm import get_llm
from ai.chains import _invoke_with_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.icons import icon

NOT_FOUND = "Not Found"
MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"

SYSTEM_PROMPT = """You are TalentAI Co-Recruiter, an expert AI hiring assistant.
Answer questions about the candidate using ONLY the provided profile data.
Be concise, professional, and direct. Use bullet points and clear structure.
If information is missing, say "Data not available".

CANDIDATE PROFILE:
Name: {name}
Education: {education}
Experience: {experience_years} years
AI Match Score: {score}/100
Recommendation: {recommendation}
Summary: {summary}
Matching Skills: {matching_skills}
Missing Skills: {missing_skills}
Extra Skills: {extra_skills}
Justification: {justification}
Technical Questions: {technical_questions}
HR Questions: {hr_questions}
"""

PRESETS = [
    ("Technical Questions", "Generate 5 tailored technical interview questions for this candidate. Include difficulty level for each."),
    ("Role Fit Audit", "Rate alignment across Technical Skills, Experience, Cultural Fit, and Growth Potential on a 1-10 scale."),
    ("Hire vs No-Hire", "Provide a structured Hire/No-Hire recommendation with top 3 reasons, concerns, mitigations, and final verdict."),
    ("Red Flags Check", "Scan for potential red flags: skill gaps, over-qualification, experience mismatches, or interview concerns."),
]

MOCK_SCHEDULE = [
    {"time": "09:00", "date": "18 Jul", "type": "interview", "title": "Technical Screen", "role": "Engineering Team", "color": "orange", "platform": "meet"},
    {"time": "11:30", "date": "18 Jul", "type": "1on1", "title": "Hiring Manager Sync", "role": "Direct Report", "color": "green", "platform": "zoom"},
    {"time": "14:00", "date": "18 Jul", "type": "interview", "title": "Culture Fit Round", "role": "HR & Team Lead", "color": "blue", "platform": "meet"},
    {"time": "16:30", "date": "18 Jul", "type": "1on1", "title": "Offer Review Call", "role": "Candidates", "color": "red", "platform": "zoom"},
]

MEET_SVG = '<svg viewBox="0 0 24 24" fill="none"><rect x="2" y="6" width="14" height="12" rx="2" fill="#34A853"/><path d="M16 9.5L22 6v12l-6-3.5z" fill="#34A853"/></svg>'
ZOOM_SVG = '<svg viewBox="0 0 24 24" fill="none"><rect x="2" y="4" width="20" height="16" rx="4" fill="#2D8CFF"/><path d="M6 8h9a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" fill="#fff"/><path d="M17 11l3.5-2v6L17 13v-2z" fill="#fff"/></svg>'


def render_ai_chat(cand: dict):
    name = cand.get("candidate_name", "Unknown")
    cid = cand.get("id", name)

    profile = {
        "name": name,
        "education": cand.get("education", NOT_FOUND),
        "experience_years": cand.get("experience_years", 0),
        "score": cand.get("score", 0),
        "recommendation": cand.get("recommendation", NOT_FOUND),
        "summary": (cand.get("summary", NOT_FOUND) or NOT_FOUND)[:500],
        "matching_skills": ", ".join(cand.get("matching_skills", []) or []) or NOT_FOUND,
        "missing_skills": ", ".join(cand.get("missing_skills", []) or []) or NOT_FOUND,
        "extra_skills": ", ".join(cand.get("extra_skills", []) or []) or NOT_FOUND,
        "justification": (cand.get("justification", NOT_FOUND) or NOT_FOUND)[:300],
        "technical_questions": ", ".join(cand.get("technical_questions", []) or []) or NOT_FOUND,
        "hr_questions": ", ".join(cand.get("hr_questions", []) or []) or NOT_FOUND,
    }

    if f"chat_{cid}" not in st.session_state:
        st.session_state[f"chat_{cid}"] = []
    chat_history = st.session_state[f"chat_{cid}"]

    # AI Panel
    st.markdown(f"""
    <div class="ai-panel">
        <div class="ai-header">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#4f46e5);display:flex;align-items:center;justify-content:center;color:white;font-size:13px;">{icon("sparkles", 14, "white")}</div>
                <div>
                    <div style="font-size:12px;font-weight:700;color:white;">AI Co-Recruiter</div>
                    <div style="font-size:9px;color:#64748b;font-family:{MONO_FONT};">Gemini 2.0 Flash</div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:5px;">
                <span class="pulse-dot"></span>
                <span style="font-size:9px;color:#64748b;font-family:{MONO_FONT};">LIVE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not chat_history:
        st.markdown(f"""
        <div style="text-align:center;padding:12px 8px;">
            <div style="width:36px;height:36px;border-radius:50%;background:#1e293b;display:inline-flex;align-items:center;justify-content:center;color:#818cf8;margin-bottom:10px;">{icon("message-square", 18, "#818cf8")}</div>
            <p style="font-size:12px;font-weight:600;color:white;margin:0;">Query {name}'s Profile</p>
            <p style="font-size:10px;color:#64748b;margin:4px 0 0 0;">Select a quick action or type a question below.</p>
        </div>
        """, unsafe_allow_html=True)

        for label, prompt_text in PRESETS:
            if st.button(label, key=f"preset_{cid}_{label}", use_container_width=True):
                chat_history.append({"role": "user", "text": prompt_text})
                with st.spinner("Analyzing..."):
                    answer = _query_ai(profile, prompt_text)
                chat_history.append({"role": "ai", "text": answer})
                st.rerun()
    else:
        for msg in chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div style="display:flex;justify-content:flex-end;margin-bottom:8px;"><div class="ai-msg-user">{msg["text"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="display:flex;justify-content:flex-start;margin-bottom:8px;"><div class="ai-msg-ai">{msg["text"]}</div></div>', unsafe_allow_html=True)

    user_input = st.chat_input(f"Ask about {name}...", key=f"chat_input_{cid}")
    if user_input:
        chat_history.append({"role": "user", "text": user_input})
        with st.spinner("Thinking..."):
            answer = _query_ai(profile, user_input)
        chat_history.append({"role": "ai", "text": answer})
        st.rerun()

    if chat_history:
        if st.button("Clear Chat", key=f"clear_{cid}", use_container_width=True):
            st.session_state[f"chat_{cid}"] = []
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ===== CALENDAR WIDGET =====
    st.markdown(render_calendar_widget(), unsafe_allow_html=True)


def render_calendar_widget() -> str:
    from datetime import date, timedelta
    import calendar as cal_mod

    today = date.today()
    year, month = today.year, today.month
    month_name = today.strftime("%B %Y")
    first_day = date(year, month, 1)
    start_weekday = (first_day.weekday()) % 7
    days_in_month = cal_mod.monthrange(year, month)[1]
    prev_month_days = cal_mod.monthrange(year, month - 1 if month > 1 else 12)[1] if month > 1 else cal_mod.monthrange(year - 1, 12)[1]

    days_html = ""
    for i in range(start_weekday):
        d = prev_month_days - start_weekday + i + 1
        days_html += f'<div class="cal-day muted">{d}</div>'

    for d in range(1, days_in_month + 1):
        cls = ""
        dt = date(year, month, d)
        if dt == today:
            cls = " today"
        elif dt.weekday() >= 5:
            cls = " weekend"
            if d > days_in_month - 3 and d != days_in_month:
                cls += " muted"
        elif d == 1:
            cls = " muted"

        dot = '<span class="dot"></span>' if d == 15 else ""
        days_html += f'<div class="cal-day{cls}">{d}{dot}</div>'

    remaining = 7 - ((start_weekday + days_in_month) % 7)
    if remaining < 7:
        for i in range(1, remaining + 1):
            days_html += f'<div class="cal-day muted">{i}</div>'

    events_html = ""
    for evt in MOCK_SCHEDULE:
        platform_svg = MEET_SVG if evt["platform"] == "meet" else ZOOM_SVG
        platform_cls = "meet" if evt["platform"] == "meet" else "zoom"
        events_html += f"""
        <div class="cal-event">
            <div class="cal-bar {evt['color']}"></div>
            <div class="cal-datetime">{evt['date']}<br>{evt['time']}</div>
            <div class="cal-info">
                <div class="cal-event-role">{evt['role']}</div>
                <div class="cal-event-title">{evt['title']}</div>
            </div>
            <div class="cal-call-icon {platform_cls}">{platform_svg}</div>
        </div>"""

    return f"""
    <div class="cal-card" style="margin-top:12px;">
        <div class="cal-header">
            <button class="cal-nav">&#8249;</button>
            <span class="month">{month_name}</span>
            <button class="cal-nav">&#8250;</button>
        </div>
        <div class="cal-weekdays">
            <span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span>
        </div>
        <div class="cal-days">{days_html}</div>
        <div class="cal-agenda">{events_html}</div>
    </div>"""


def _query_ai(profile: dict, question: str) -> str:
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}"),
        ])
        llm = get_llm(temperature=0.3)
        chain = prompt | llm | StrOutputParser()
        return _invoke_with_retry(chain, {"question": question, **profile})
    except Exception as e:
        return f"AI unavailable: {e}"
