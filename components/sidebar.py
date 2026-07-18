import os
import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 2rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin: 0;
    }

    /* Metric cards */
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card h3 {
        font-size: 1.8rem;
        margin: 0;
        color: #667eea;
    }
    .metric-card p {
        color: #6c757d;
        font-size: 0.85rem;
        margin: 0.3rem 0 0 0;
    }

    /* Section headers */
    .section-divider {
        border-top: 2px solid #e9ecef;
        margin: 1.5rem 0;
    }
    .section-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #6c757d;
        margin-bottom: 0.5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #fafbfc;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #667eea;
    }

    /* Skill badges */
    .skill-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.15rem;
        font-weight: 500;
    }
    .skill-match { background: #d4edda; color: #155724; }
    .skill-miss  { background: #f8d7da; color: #721c24; }
    .skill-extra { background: #d1ecf1; color: #0c5460; }

    /* Expander styling */
    .stExpander {
        border: 1px solid #e9ecef;
        border-radius: 8px;
    }

    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    inject_custom_css()

    with st.sidebar:
        st.markdown("### :gear[Settings]")

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

        st.markdown("### :blue_book[How to Use]")
        st.markdown(
            """
            1. Upload a **Job Description** (PDF)
            2. Upload one or more **Resumes** (PDF)
            3. Click **Analyze Resumes**
            4. Review rankings, compare candidates, export CSV
            """
        )

        st.markdown("---")

        st.markdown("### :information_source[About]")
        st.caption(
            "AI-powered resume screening built with "
            "**LangChain + Gemini + Supabase**. "
            "Results are persisted to Supabase for history tracking."
        )
        st.caption("SMIT Batch 9 — Final Project")

        st.markdown("---")

        if st.checkbox("Check DB Status", key="show_db"):
            try:
                from ai.db import get_client
                client = get_client()
                result = client.table("candidates").select("id", count="exact").execute()
                count = result.count or 0
                st.success(f"Connected — {count} candidates stored")
            except Exception as e:
                st.error(f"DB error: {e}")
