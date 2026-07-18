from __future__ import annotations
import streamlit as st
from utils.pdf_reader import extract_text, ExtractionResult
from utils.icons import icon

NOT_FOUND = "Not Found"
MONO_FONT = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"


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


def render_upload_page():
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;padding:32px 24px;">
        <div style="max-width:800px;width:100%;">
            <div style="text-align:center;margin-bottom:32px;">
                <div style="width:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,#6366f1,#4f46e5);
                            display:inline-flex;align-items:center;justify-content:center;margin-bottom:16px;">
                    {icon("upload", 24, "white")}
                </div>
                <h2 style="font-size:20px;font-weight:700;color:#0f172a;margin:0;">Upload Documents</h2>
                <p style="font-size:13px;color:#94a3b8;margin:6px 0 0 0;">Upload a Job Description and candidate Resumes to begin AI-powered analysis.</p>
            </div>
            <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:24px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    {icon("file-text", 16, "#4f46e5")}
                    <span style="font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#94a3b8;font-family:{MONO_FONT};font-weight:600;">Job Description</span>
                    <span style="font-size:10px;color:#94a3b8;font-family:{MONO_FONT};margin-left:auto;">PDF only</span>
                </div>
    """, unsafe_allow_html=True)

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
                st.success(f"Extracted - {result.page_count} page{'s' if result.page_count != 1 else ''}")
                with st.expander("Preview JD text"):
                    st.text_area("JD", jd_text, height=160, disabled=True, key="jd_view")
            else:
                st.warning(result.warning or NOT_FOUND)

    st.markdown(f"""
            </div>
            <div style="height:16px;"></div>
            <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:24px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    {icon("users", 16, "#4f46e5")}
                    <span style="font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#94a3b8;font-family:{MONO_FONT};font-weight:600;">Resumes</span>
                    <span style="font-size:10px;color:#94a3b8;font-family:{MONO_FONT};margin-left:auto;">PDF | Max 10 MB each</span>
                </div>
    """, unsafe_allow_html=True)

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

    st.markdown("</div></div></div>", unsafe_allow_html=True)

    return jd_text, resume_texts
