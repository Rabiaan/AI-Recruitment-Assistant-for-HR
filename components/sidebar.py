import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Google API Key", type="password", key="api_key")
        if api_key:
            import os
            os.environ["GOOGLE_API_KEY"] = api_key
        st.markdown("---")
        st.markdown("### About")
        st.write(
            "AI Recruitment Assistant analyzes resumes against a job description "
            "and produces structured candidate rankings."
        )
