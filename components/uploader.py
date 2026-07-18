import streamlit as st
from utils.pdf_reader import extract_text, ExtractionResult

NOT_FOUND = "Not Found"


def _validate_pdf(file) -> str | None:
    if file is None:
        return "No file provided."
    if not file.name.lower().endswith(".pdf"):
        return f"{file.name} is not a PDF."
    if file.size == 0:
        return f"{file.name} is empty."
    if file.size > 10 * 1024 * 1024:
        return f"{file.name} exceeds 10 MB."
    return None


def render_uploader():
    col_jd, col_res = st.columns(2)

    with col_jd:
        st.markdown('<p class="section-mono">&#128196; Job Description</p>', unsafe_allow_html=True)
        jd_file = st.file_uploader("Upload JD PDF", type=["pdf"], key="jd_uploader", label_visibility="collapsed")

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
                    st.success(f"Extracted — {result.page_count} page{'s' if result.page_count != 1 else ''}")
                    with st.expander("Preview JD text"):
                        st.text_area("JD", jd_text, height=160, disabled=True, key="jd_view")
                else:
                    st.warning(result.warning or NOT_FOUND)

    with col_res:
        st.markdown('<p class="section-mono">&#128203; Resumes</p>', unsafe_allow_html=True)
        resume_files = st.file_uploader("Upload Resumes", type=["pdf"], accept_multiple_files=True, key="resume_uploader", label_visibility="collapsed")

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
                    skipped.append(f"{file.name}: {result.warning or NOT_FOUND}")

            if resume_texts:
                st.success(f"{len(resume_texts)} resume{'s' if len(resume_texts) != 1 else ''} ready")
                with st.expander(f"Preview resumes ({len(resume_texts)})"):
                    for name, text in resume_texts:
                        st.markdown(f"**{name}**")
                        st.text_area(name, text, height=100, disabled=True, key=f"rv_{name}", label_visibility="collapsed")

            if skipped:
                with st.expander(f"Skipped ({len(skipped)})"):
                    for msg in skipped:
                        st.warning(msg)

    return jd_text, resume_texts
