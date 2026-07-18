from __future__ import annotations
import streamlit as st
from ai.llm import get_llm
from ai.chains import _invoke_with_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

NOT_FOUND = "Not Found"

SYSTEM_PROMPT = """You are TalentAI Co-Recruiter, an AI hiring assistant.
Answer questions about the candidate below using ONLY the provided profile data.
Be concise, professional, and direct. If information is missing, say so.

CANDIDATE PROFILE:
Name: {name}
Education: {education}
Experience: {experience_years} years
Score: {score}/100
Recommendation: {recommendation}
Summary: {summary}
Matching Skills: {matching_skills}
Missing Skills: {missing_skills}
Extra Skills: {extra_skills}
Justification: {justification}
Technical Questions: {technical_questions}
HR Questions: {hr_questions}
"""

PRESET_QUERIES = {
    "questions": "Generate 3 technical interview questions tailored to this candidate's skills and the role requirements.",
    "fit": "Evaluate this candidate's overall fit for the role. What are the strongest indicators and biggest concerns?",
    "strengths": "What are the top 3 strengths of this candidate based on their profile?",
}


def render_ai_chat(cand: dict):
    name = cand.get("candidate_name", "Unknown")
    cid = cand.get("id", name)

    # Build profile context
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

    # Initialize chat history
    if f"chat_{cid}" not in st.session_state:
        st.session_state[f"chat_{cid}"] = []

    chat_history = st.session_state[f"chat_{cid}"]

    # Panel header
    st.markdown(f"""
    <div class="ai-panel">
        <div class="ai-header">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:28px;height:28px;border-radius:8px;background:#4f46e5;display:flex;align-items:center;justify-content:center;color:white;font-size:14px;">&#10024;</div>
                <div>
                    <div style="font-size:12px;font-weight:700;">AI Co-Recruiter</div>
                    <div style="font-size:9px;color:#64748b;font-family:ui-monospace,'Cascadia Code','Source Code Pro',Menlo,Consolas,monospace;">Gemini Flash Active</div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:4px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#10b981;animation:pulse 2s infinite;"></span>
                <span style="font-size:9px;color:#64748b;font-family:ui-monospace,'Cascadia Code','Source Code Pro',Menlo,Consolas,monospace;">LIVE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Chat messages
    if not chat_history:
        st.markdown(f"""
        <div style="text-align:center;padding:24px 8px;">
            <div style="width:40px;height:40px;border-radius:50%;background:#1e293b;display:inline-flex;align-items:center;justify-content:center;color:#818cf8;margin-bottom:12px;">&#128172;</div>
            <p style="font-size:12px;font-weight:600;color:#e2e8f0;margin:0;">Query Candidate Profile</p>
            <p style="font-size:10px;color:#64748b;margin:6px 0 0 0;">Ask about {name}'s qualifications or career fit.</p>
        </div>
        """, unsafe_allow_html=True)

        for key, label in PRESET_QUERIES.items():
            if st.button(label, key=f"preset_{cid}_{key}", use_container_width=True):
                chat_history.append({"role": "user", "text": label})
                with st.spinner("Analyzing..."):
                    answer = _query_ai(profile, label)
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

    # Input
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
