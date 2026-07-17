import os
from datetime import datetime
import pandas as pd
import streamlit as st
from components.uploader import render_uploader
from components.sidebar import render_sidebar
from components.ranking import render_ranking
from ai.chains import (
    build_summary_chain,
    build_skill_match_chain,
    build_score_chain,
    build_hr_chain,
    build_interview_questions_chain,
    parse_score,
    _invoke_with_retry,
)


def analyze_resume(resume_name: str, resume_text: str, jd_text: str):
    try:
        summary_chain = build_summary_chain()
        skill_match_chain = build_skill_match_chain()
        score_chain = build_score_chain()
        hr_chain = build_hr_chain()
        questions_chain = build_interview_questions_chain()

        summary = _invoke_with_retry(summary_chain, resume_text)
        skill_match = _invoke_with_retry(skill_match_chain, {"jd_text": jd_text, "resume_text": resume_text})
        raw_score = _invoke_with_retry(score_chain, {"jd_text": jd_text, "skill_match": skill_match})
        score = parse_score(raw_score)

        recommendation_text = _invoke_with_retry(hr_chain, {
            "score": str(score),
            "missing_skills": "Extract missing skills from: " + skill_match,
        })

        recommendation, *justification_parts = recommendation_text.split("\n", 1)
        justification = justification_parts[0].strip() if justification_parts else recommendation_text

        if score >= 60:
            questions_text = _invoke_with_retry(questions_chain, {
                "jd_text": jd_text,
                "summary": summary,
            })
            questions = {"technical_and_hr": [q.strip() for q in questions_text.split("\n") if q.strip()]}
        else:
            questions = {}

        matching = []
        missing = []
        extra = []
        skill_section = None
        current_list = None
        for line in skill_match.split("\n"):
            line_lower = line.lower()
            if "matching skills" in line_lower:
                skill_section = "matching"
                current_list = matching
                continue
            elif "missing skills" in line_lower:
                skill_section = "missing"
                current_list = missing
                continue
            elif "extra skills" in line_lower:
                skill_section = "extra"
                current_list = extra
                continue
            if current_list is not None and line.strip().startswith("-"):
                current_list.append(line.strip()[1:].strip())

        return {
            "name": resume_name,
            "summary": summary.strip(),
            "matching_skills": matching,
            "missing_skills": missing,
            "extra_skills": extra,
            "score": score,
            "recommendation": recommendation.strip(),
            "justification": justification.strip(),
            "interview_questions": questions,
        }
    except Exception as e:
        st.error(f"Error analyzing {resume_name}: {e}")
        return {
            "name": resume_name,
            "summary": "Analysis failed",
            "matching_skills": [],
            "missing_skills": [],
            "extra_skills": [],
            "score": 0,
            "recommendation": "Review Needed",
            "justification": str(e),
            "interview_questions": {},
        }


def export_results(results, filename_prefix="candidate_analysis"):
    if not results:
        st.warning("No results to export.")
        return None
    df = pd.DataFrame(results)
    df["matching_skills"] = df["matching_skills"].apply(lambda x: "; ".join(x))
    df["missing_skills"] = df["missing_skills"].apply(lambda x: "; ".join(x))
    df["extra_skills"] = df["extra_skills"].apply(lambda x: "; ".join(x))
    df["interview_questions"] = df["interview_questions"].apply(lambda x: " | ".join([f"{k}: {', '.join(v)}" for k, v in x.items()]) if x else "")

    csv_buffer = df.to_csv(index=False).encode("utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("outputs", f"{filename_prefix}_{timestamp}.csv")
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(csv_buffer)

    return csv_buffer, output_path


def main():
    st.set_page_config(page_title="AI Recruitment Assistant", layout="wide")
    render_sidebar()

    st.title("AI Recruitment Assistant Dashboard")
    st.markdown("Upload a job description and resumes to get AI-powered candidate analysis.")

    jd_text, resume_texts = render_uploader()

    analyze_clicked = st.button(
        "Analyze Resumes",
        disabled=(not jd_text or len(resume_texts) == 0),
        type="primary",
    )

    if analyze_clicked:
        if "results" not in st.session_state:
            st.session_state.results = []

        st.session_state.resumes = [r[0] for r in resume_texts]
        st.session_state.jd_text = jd_text

        results = []
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        for idx, (name, text) in enumerate(resume_texts):
            status_text.text(f"Analyzing {name} ({idx + 1}/{len(resume_texts)})...")
            result = analyze_resume(name, text, jd_text)
            results.append(result)
            progress_bar.progress((idx + 1) / len(resume_texts))

        st.session_state.results = results
        status_text.text("Analysis complete.")

    if "results" in st.session_state and st.session_state.results:
        render_ranking(st.session_state.results)

        st.markdown("---")
        st.subheader("Export Results")
        if st.button("Download CSV"):
            csv_buffer, output_path = export_results(st.session_state.results)
            if csv_buffer:
                st.download_button(
                    label="Click to download CSV",
                    data=csv_buffer,
                    file_name=os.path.basename(output_path),
                    mime="text/csv",
                )
                st.success(f"Saved copy to {output_path}")


if __name__ == "__main__":
    main()
