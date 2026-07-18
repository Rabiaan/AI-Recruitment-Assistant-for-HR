import streamlit as st
from utils.pdf_reader import extract_text, ExtractionResult


def _validate_pdf(file) -> str | None:
    if file is None:
        return "No file provided."
    if not file.name.lower().endswith(".pdf"):
        return f"{file.name} is not a PDF file."
    if file.size == 0:
        return f"{file.name} is empty (0 bytes)."
    if file.size > 10 * 1024 * 1024:
        return f"{file.name} exceeds 10 MB size limit."
    return None


def render_uploader():
    st.subheader("1. Upload Job Description")
    jd_file = st.file_uploader(
        "Select a Job Description PDF",
        type=["pdf"],
        key="jd_uploader",
        help="Upload a single PDF containing the job description.",
    )

    jd_text = ""
    if jd_file is not None:
        error = _validate_pdf(jd_file)
        if error:
            st.warning(error)
        else:
            jd_file.seek(0)
            result: ExtractionResult = extract_text(jd_file)
            if result.success:
                jd_text = result.text
                st.success(f"JD extracted ({result.page_count} page{'s' if result.page_count != 1 else ''})")
                with st.expander("View Extracted JD Text"):
                    st.text_area("JD Content", jd_text, height=200, disabled=True, key="jd_text_view")
            else:
                st.warning(result.warning or "Could not extract text from JD.")

    st.subheader("2. Upload Resumes")
    resume_files = st.file_uploader(
        "Select Resume PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="resume_uploader",
        help="Upload one or more PDF resumes. Max 10 MB each.",
    )

    resume_texts: list[tuple[str, str]] = []
    skipped: list[str] = []

    if resume_files:
        for file in resume_files:
            error = _validate_pdf(file)
            if error:
                skipped.append(f"{file.name}: {error}")
                continue

            file.seek(0)
            result: ExtractionResult = extract_text(file)
            if result.success:
                resume_texts.append((file.name, result.text))
            else:
                skipped.append(f"{file.name}: {result.warning or 'Could not extract text'}")

        if resume_texts:
            st.success(f"{len(resume_texts)} resume{'s' if len(resume_texts) != 1 else ''} ready for analysis")
            with st.expander(f"View Extracted Resumes ({len(resume_texts)})"):
                for name, text in resume_texts:
                    st.markdown(f"**{name}**")
                    st.text_area(
                        name,
                        text,
                        height=150,
                        disabled=True,
                        key=f"resume_view_{name}",
                        label_visibility="collapsed",
                    )

        if skipped:
            with st.expander(f"Skipped Files ({len(skipped)})", expanded=False):
                for msg in skipped:
                    st.warning(msg)

    return jd_text, resume_texts
