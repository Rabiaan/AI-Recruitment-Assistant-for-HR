import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment variables. Check your .env file."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
        max_retries=2,
        request_timeout=60,
    )
