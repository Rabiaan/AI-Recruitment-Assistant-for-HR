import pandas as pd
import streamlit as st


def _color_recommendation(val: str) -> str:
    colors = {
        "Hire": "background-color: #d4edda; color: #155724; font-weight: 700",
        "Interview": "background-color: #fff3cd; color: #856404; font-weight: 700",
        "Reject": "background-color: #f8d7da; color: #721c24; font-weight: 700",
        "Error - manual review needed": "background-color: #e2e3e5; color: #383d41; font-weight: 700",
    }
    return colors.get(val, "")


def _render_score_gauge(score: int) -> str:
    if score >= 85:
        color, emoji = "#28a745", ""
    elif score >= 65:
        color, emoji = "#ffc107", ""
    else:
        color, emoji = "#dc3545", ""
    return f'<span style="color:{color};font-weight:700;font-size:1.1rem">{emoji} {score}/100</span>'


def render_ranking(results: list[dict]):
    if not results:
        st.info("No results to display yet.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)

    st.markdown("---")

    hire_count = len(df[df["recommendation"] == "Hire"])
    interview_count = len(df[df["recommendation"] == "Interview"])
    reject_count = len(df[df["recommendation"] == "Reject"])
    avg_score = int(df["score"].mean())

    st.markdown("#### :trophy: Analysis Results")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Candidates", len(df))
    with c2:
        st.metric("Avg Score", avg_score)
    with c3:
        st.metric("Hire", hire_count, delta=None, delta_color="normal")
    with c4:
        st.metric("Interview", interview_count)

    st.markdown("")

    display_df = df[["rank", "candidate_name", "score", "recommendation", "justification"]].copy()
    display_df.columns = ["#", "Candidate", "Score", "Recommendation", "Justification"]

    styled = display_df.style.apply(
        lambda row: [_color_recommendation(row["Recommendation"]) if col == "Recommendation" else "" for col in row.index],
        axis=1,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=min(38 * len(display_df) + 40, 420))

    st.markdown("")
    _render_comparison(df)
    _render_expanders(df)


def _render_comparison(df: pd.DataFrame):
    if len(df) < 2:
        return

    st.markdown("#### :balance_scale: Candidate Comparison")
    selected = st.multiselect(
        "Select 2-3 candidates to compare side-by-side",
        options=df["candidate_name"].tolist(),
        default=[],
        max_selections=3,
        key="compare_select",
        label_visibility="collapsed",
        placeholder="Choose candidates to compare...",
    )

    if len(selected) < 2:
        st.caption("Select at least 2 candidates above to compare.")
        return

    cols = st.columns(len(selected))
    for col, name in zip(cols, selected):
        row = df[df["candidate_name"] == name].iloc[0]
        with col:
            with st.container(border=True):
                st.markdown(f"**{name}**")
                score = row["score"]
                rec = row["recommendation"]

                st.markdown(_render_score_gauge(score), unsafe_allow_html=True)

                rec_colors = {"Hire": "green", "Interview": "orange", "Reject": "red"}
                rc = rec_colors.get(rec, "gray")
                st.markdown(f":{rc}[**{rec}**]")

                st.markdown(f"**Education:** {row.get('education', 'N/A')}")
                st.markdown(f"**Experience:** {row.get('experience_years', 0)} years")

                matching = row.get("matching_skills", []) or []
                missing = row.get("missing_skills", []) or []
                extra = row.get("extra_skills", []) or []

                if matching:
                    st.markdown("**Matching** " + " ".join(
                        [f"`{s}`" for s in matching]
                    ))
                if missing:
                    st.markdown("**Missing** " + " ".join(
                        [f"~~{s}~~" for s in missing]
                    ))
                if extra:
                    st.markdown("**Bonus** " + " ".join(
                        [f"+{s}" for s in extra]
                    ))


def _render_expanders(df: pd.DataFrame):
    st.markdown("#### :busts_in_silhouette: Candidate Details")

    for _, row in df.iterrows():
        name = row["candidate_name"]
        score = row["score"]
        rec = row["recommendation"]

        rec_emoji = {"Hire": "✅", "Interview": "🟡", "Reject": "❌"}.get(rec, "⚪")

        with st.expander(f"{rec_emoji} {name} — Score: {score} | {rec}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Summary**")
                st.write(row.get("summary", "N/A"))
                st.markdown("**Education**")
                st.write(row.get("education", "N/A"))
                st.markdown("**Experience**")
                st.write(f"{row.get('experience_years', 0)} years")

            with col2:
                matching = row.get("matching_skills", []) or []
                missing = row.get("missing_skills", []) or []
                extra = row.get("extra_skills", []) or []

                st.markdown("**Matching Skills**")
                st.write(", ".join(matching) if matching else "None")
                st.markdown("**Missing Skills**")
                st.write(", ".join(missing) if missing else "None")
                st.markdown("**Extra Skills**")
                st.write(", ".join(extra) if extra else "None")

            st.markdown("**Justification**")
            st.info(row.get("justification", "N/A"))

            technical = row.get("technical_questions", []) or []
            hr = row.get("hr_questions", []) or []
            if technical or hr:
                st.markdown("---")
                qcol1, qcol2 = st.columns(2)
                with qcol1:
                    if technical:
                        st.markdown("**Technical Questions**")
                        for i, q in enumerate(technical, 1):
                            st.markdown(f"{i}. {q}")
                with qcol2:
                    if hr:
                        st.markdown("**HR / Behavioral Questions**")
                        for i, q in enumerate(hr, 1):
                            st.markdown(f"{i}. {q}")
