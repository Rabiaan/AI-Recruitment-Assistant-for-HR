from __future__ import annotations
import streamlit as st
from ai.llm import get_llm
from ai.chains import _invoke_with_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

NOT_FOUND = "Not Found"

MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"

SYSTEM_PROMPT = """You are TalentAI Co-Recruiter, an expert AI hiring assistant for TalentAI HR Intelligence Workspace.
You help hiring managers evaluate candidates using ONLY the provided profile data.
Be concise, professional, data-driven, and direct. Structure responses with clear headings and bullet points.
If information is missing, explicitly state "Data not available" rather than guessing.

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

PRESET_QUERIES = [
    ("Technical Questions", "Generate 5 tailored technical interview questions for this candidate based on their skills and the role requirements. Include difficulty level for each."),
    ("Role Fit Audit", "Perform a comprehensive role-fit analysis. Rate alignment across Technical Skills, Experience Level, Cultural Fit, and Growth Potential on a 1-10 scale with brief justification."),
    ("Hire vs No-Hire", "Provide a structured Hire / No-Hire recommendation with: (1) Top 3 reasons to hire, (2) Top 3 concerns, (3) Suggested mitigations, (4) Final verdict with confidence level."),
    ("Red Flags Check", "Scan the candidate profile for potential red flags: gaps in skills, over-qualification risks, experience mismatches, or any concerns that need addressing in interviews."),
]

MOCK_SCHEDULE = [
    {"time": "09:00 AM", "type": "interview", "title": "Technical Screen", "participant": "Engineering Team", "link": "#"},
    {"time": "11:30 AM", "type": "1on1", "title": "Hiring Manager Sync", "participant": "Direct Report", "link": "#"},
    {"time": "02:00 PM", "type": "interview", "title": "Culture Fit Round", "participant": "HR & Team Lead", "link": "#"},
    {"time": "04:30 PM", "type": "1on1", "title": "Offer Review Call", "participant": "Candidates", "link": "#"},
]


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

    # AI Panel Header
    st.markdown(f"""
    <div class="ai-panel">
        <div class="ai-header">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#4f46e5);display:flex;align-items:center;justify-content:center;color:white;font-size:13px;">&#10024;</div>
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

    # Preset buttons when no chat
    if not chat_history:
        st.markdown(f"""
        <div style="text-align:center;padding:16px 8px 12px;">
            <div style="width:36px;height:36px;border-radius:50%;background:#1e293b;display:inline-flex;align-items:center;justify-content:center;color:#818cf8;margin-bottom:10px;font-size:16px;">&#128172;</div>
            <p style="font-size:12px;font-weight:600;color:white;margin:0;">Query {name}'s Profile</p>
            <p style="font-size:10px;color:#64748b;margin:4px 0 0 0;">Select a quick action or type a custom question below.</p>
        </div>
        """, unsafe_allow_html=True)

        for label, prompt_text in PRESET_QUERIES:
            if st.button(label, key=f"preset_{cid}_{label}", use_container_width=True):
                chat_history.append({"role": "user", "text": prompt_text})
                with st.spinner("Analyzing..."):
                    answer = _query_ai(profile, prompt_text)
                chat_history.append({"role": "ai", "text": answer})
                st.rerun()
    else:
        chat_container = st.container()
        with chat_container:
            for msg in chat_history:
                if msg["role"] == "user":
                    st.markdown(f'<div style="display:flex;justify-content:flex-end;margin-bottom:8px;"><div class="ai-msg-user">{msg["text"]}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="display:flex;justify-content:flex-start;margin-bottom:8px;"><div class="ai-msg-ai">{msg["text"]}</div></div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input(f"Ask about {name}...", key=f"chat_input_{cid}")
    if user_input:
        chat_history.append({"role": "user", "text": user_input})
        with st.spinner("Thinking..."):
            answer = _query_ai(profile, user_input)
        chat_history.append({"role": "ai", "text": answer})
        st.rerun()

    # Clear button
    if chat_history:
        if st.button("Clear Chat", key=f"clear_{cid}", use_container_width=True):
            st.session_state[f"chat_{cid}"] = []
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ========== TODAY'S INTERVIEW SCHEDULE ==========
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:14px;">&#128197;</span>
                <span style="font-size:12px;font-weight:700;color:#0f172a;">Today's Schedule</span>
            </div>
            <span style="font-size:10px;color:#94a3b8;font-family:{MONO_FONT};">4 Events</span>
        </div>
    """, unsafe_allow_html=True)

    for item in MOCK_SCHEDULE:
        type_cls = "type-interview" if item["type"] == "interview" else "type-1on1"
        type_label = "Interview" if item["type"] == "interview" else "1-on-1"
        st.markdown(f"""
        <div class="schedule-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div class="schedule-time">{item['time']}</div>
                    <div class="schedule-title">{item['title']}</div>
                    <div class="schedule-meta">{item['participant']}</div>
                    <span class="schedule-type {type_cls}">{type_label}</span>
                </div>
                <a href="{item['link']}" target="_blank"
                   style="display:inline-flex;align-items:center;gap:4px;padding:6px 10px;background:#4f46e5;color:white;border-radius:6px;font-size:10px;font-weight:600;text-decoration:none;transition:opacity 0.15s;margin-top:4px;">
                    &#128249; Join
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


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
