import os
import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.header("AI Recruitment Assistant")

        st.subheader("Settings")
        api_key = st.text_input(
            "Google API Key",
            type="password",
            key="api_key_input",
            value=os.getenv("GOOGLE_API_KEY", ""),
            help="Your Gemini API key. Also set via .env file.",
        )
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

        model = st.selectbox(
            "Gemini Model",
            ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"],
            key="model_select",
        )
        if model:
            os.environ["GEMINI_MODEL"] = model

        st.markdown("---")

        st.subheader("How to Use")
        st.markdown(
            "1. Upload a **Job Description** (PDF)\n"
            "2. Upload one or more **Resumes** (PDF)\n"
            "3. Click **Analyze Resumes**\n"
            "4. Review rankings, compare candidates, export CSV"
        )

        st.markdown("---")

        st.subheader("About")
        st.caption(
            "AI-powered resume screening using Gemini LLM. "
            "Results are persisted to Supabase for history tracking."
        )

        if st.checkbox("Show DB Status", key="show_db"):
            try:
                from ai.db import get_client

                client = get_client()
                result = client.table("candidates").select("id", count="exact").execute()
                count = result.count or 0
                st.success(f"Connected — {count} candidates in DB")
            except Exception as e:
                st.error(f"DB error: {e}")
