import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str) -> str | None:
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name, None)
    except Exception:
        return None


def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    api_key = _get_env("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Set it in .env (local) or Streamlit Cloud Secrets."
        )

    model = _get_env("GEMINI_MODEL") or "gemini-2.0-flash"

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
        max_retries=3,
        request_timeout=120,
    )
