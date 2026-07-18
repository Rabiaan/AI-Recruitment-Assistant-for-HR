import streamlit as st
from utils.pdf_reader import extract_text


def render_uploader():
    st.subheader("1. Upload Job Description")
    jd_file = st.file_uploader("JD (PDF)", type=["pdf"], key="jd_uploader")
    jd_text = extract_text(jd_file) if jd_file else ""
    if jd_file:
        if jd_text:
            st.success("JD extracted successfully.")
            with st.expander("View Extracted Text"):
                st.text(jd_text)
        else:
            st.warning("Could not extract text from the uploaded JD. Ensure it is not a scanned PDF.")

    st.subheader("2. Upload Resumes")
    resume_files = st.file_uploader(
        "Resumes (PDF)", type=["pdf"], accept_multiple_files=True, key="resume_uploader"
    )
    resume_texts = []
    for file in resume_files:
        file.seek(0)
        text = extract_text(file)
        if text:
            resume_texts.append((file.name, text))
            with st.expander(f"View Extracted Text - {file.name}"):
                st.text(text)
        else:
            st.warning(f"Skipped {file.name}: could not extract text or it is a scanned PDF.")
    return jd_text, resume_texts
