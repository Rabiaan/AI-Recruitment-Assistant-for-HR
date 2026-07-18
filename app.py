import os
from datetime import datetime

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar, inject_custom_css
from components.uploader import render_uploader
from components.ranking import render_ranking
from ai.chains import (
    build_summary_chain,
    build_skill_match_chain,
    build_score_chain,
    build_hr_chain,
    build_interview_questions_chain,
    parse_score,
    parse_recommendation,
    parse_skill_lists,
    parse_interview_questions,
    _invoke_with_retry,
)
from utils.parser import CandidateResult, build_candidate_result


def analyze_resume(
    resume_name: str,
    resume_text: str,
    jd_text: str,
) -> CandidateResult:
    try:
        summary_chain = build_summary_chain()
        skill_match_chain = build_skill_match_chain()
        score_chain = build_score_chain()
        hr_chain = build_hr_chain()
        questions_chain = build_interview_questions_chain()

        summary = _invoke_with_retry(summary_chain, {"resume_text": resume_text})

        skill_match = _invoke_with_retry(
            skill_match_chain, {"jd_text": jd_text, "resume_text": resume_text}
        )

        score_text = _invoke_with_retry(
            score_chain, {"jd_text": jd_text, "skill_match": skill_match}
        )

        _, missing, _ = parse_skill_lists(skill_match)
        score = parse_score(score_text)

        hr_text = _invoke_with_retry(
            hr_chain,
            {
                "score": str(score),
                "missing_skills": ", ".join(missing),
                "skill_match": skill_match,
            },
        )

        interview_text = ""
        rec, _ = parse_recommendation(hr_text)
        if rec.lower() in ("hire", "interview"):
            interview_text = _invoke_with_retry(
                questions_chain, {"jd_text": jd_text, "summary": summary}
            )

        return build_candidate_result(
            candidate_name=resume_name,
            summary_text=summary,
            skill_match_text=skill_match,
            score_text=score_text,
            hr_text=hr_text,
            interview_text=interview_text,
        )

    except Exception as e:
        return CandidateResult(
            candidate_name=resume_name,
            recommendation="Error - manual review needed",
            justification=f"Analysis failed: {e}",
        )


def persist_to_supabase(jd_id: str, results: list[CandidateResult], resume_texts: dict[str, str]):
    try:
        from ai.db import insert_candidate_result
        for r in results:
            insert_candidate_result(
                jd_id=jd_id,
                candidate_name=r.candidate_name,
                resume_text=resume_texts.get(r.candidate_name, ""),
                summary=r.summary,
                education=r.education,
                experience_years=r.experience_years,
                matching_skills=r.matching_skills,
                missing_skills=r.missing_skills,
                extra_skills=r.extra_skills,
                score=r.score,
                recommendation=r.recommendation,
                justification=r.justification,
                technical_questions=r.technical_questions,
                hr_questions=r.hr_questions,
            )
        return True
    except Exception as e:
        st.warning(f"Could not persist to Supabase: {e}")
        return False


def export_csv(results: list[CandidateResult]) -> tuple[bytes, str]:
    rows = []
    for r in results:
        rows.append({
            "Name": r.candidate_name,
            "Score": r.score,
            "Recommendation": r.recommendation,
            "Summary": r.summary,
            "Education": r.education,
            "Experience (yrs)": r.experience_years,
            "Matching Skills": "; ".join(r.matching_skills),
            "Missing Skills": "; ".join(r.missing_skills),
            "Extra Skills": "; ".join(r.extra_skills),
            "Justification": r.justification,
            "Technical Questions": " | ".join(r.technical_questions),
            "HR Questions": " | ".join(r.hr_questions),
        })
    df = pd.DataFrame(rows).sort_values("Score", ascending=False)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"candidate_analysis_{timestamp}.csv"

    os.makedirs("outputs", exist_ok=True)
    with open(os.path.join("outputs", filename), "wb") as f:
        f.write(csv_bytes)

    return csv_bytes, filename


def main():
    st.set_page_config(
        page_title="AI Recruitment Assistant",
        page_icon=":briefcase:",
        layout="wide",
    )
    render_sidebar()

    st.markdown("""
    <div class="main-header">
        <h1>AI Recruitment Assistant</h1>
        <p>Upload a job description and resumes to get AI-powered candidate analysis</p>
    </div>
    """, unsafe_allow_html=True)

    jd_text, resume_tuples = render_uploader()

    st.markdown("")
    analyze_clicked = st.button(
        "Analyze Resumes",
        type="primary",
        disabled=(not jd_text or len(resume_tuples) == 0),
        use_container_width=True,
    )

    if analyze_clicked:
        resume_map = {name: text for name, text in resume_tuples}
        results: list[CandidateResult] = []

        progress = st.progress(0.0, text="Starting analysis...")
        status = st.empty()

        for idx, (name, text) in enumerate(resume_tuples):
            status.info(f"Analyzing **{name}** ({idx + 1}/{len(resume_tuples)})...")
            result = analyze_resume(name, text, jd_text)
            results.append(result)
            progress.progress(
                (idx + 1) / len(resume_tuples),
                text=f"Completed {idx + 1}/{len(resume_tuples)}",
            )

        status.success(f"Analysis complete — {len(results)} candidates processed.")
        st.session_state.results = [r.model_dump() for r in results]

        jd_title = resume_tuples[0][0] if resume_tuples else "Uploaded JD"
        try:
            from ai.db import insert_job_description
            jd_row = insert_job_description(title=jd_title, raw_text=jd_text)
            persist_to_supabase(jd_row["id"], results, resume_map)
        except Exception as e:
            st.warning(f"Supabase persistence skipped: {e}")

    if "results" in st.session_state and st.session_state.results:
        render_ranking(st.session_state.results)

        st.markdown("---")
        st.markdown("#### :floppy_disk: Export")
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Generate CSV", use_container_width=True):
                results = [CandidateResult(**r) for r in st.session_state.results]
                csv_bytes, filename = export_csv(results)
                st.download_button(
                    label="Download CSV Report",
                    data=csv_bytes,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True,
                )

        with col2:
            try:
                from ai.db import fetch_history
                history = fetch_history(limit=50)
                if history:
                    with st.expander(f":clock3: Previous Analyses ({len(history)} records)"):
                        hist_df = pd.DataFrame(history)
                        cols = ["candidate_name", "score", "recommendation", "created_at"]
                        available = [c for c in cols if c in hist_df.columns]
                        st.dataframe(hist_df[available], use_container_width=True, hide_index=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()
