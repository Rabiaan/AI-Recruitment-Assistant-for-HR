import pandas as pd
import streamlit as st


def _color_recommendation(val: str) -> str:
    colors = {
        "Hire": "background-color: #d4edda; color: #155724; font-weight: 600",
        "Interview": "background-color: #fff3cd; color: #856404; font-weight: 600",
        "Reject": "background-color: #f8d7da; color: #721c24; font-weight: 600",
        "Error - manual review needed": "background-color: #e2e3e5; color: #383d41; font-weight: 600",
    }
    return colors.get(val, "")


def render_ranking(results: list[dict]):
    if not results:
        st.info("No results to display yet.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)

    st.subheader("Candidate Ranking")

    display_df = df[["rank", "candidate_name", "score", "recommendation", "justification"]].copy()
    display_df.columns = ["Rank", "Candidate", "Score", "Recommendation", "Justification"]

    styled = display_df.style.apply(
        lambda row: [_color_recommendation(row["Recommendation"]) if col == "Recommendation" else "" for col in row.index],
        axis=1,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=min(35 * len(display_df) + 40, 400))

    st.markdown("---")
    _render_comparison(df)

    st.markdown("---")
    _render_expanders(df)


def _render_comparison(df: pd.DataFrame):
    if len(df) < 2:
        return

    st.subheader("Candidate Comparison")
    selected = st.multiselect(
        "Select 2-3 candidates to compare side-by-side",
        options=df["candidate_name"].tolist(),
        default=[],
        max_selections=3,
        key="compare_select",
    )

    if len(selected) < 2:
        st.caption("Select at least 2 candidates to compare.")
        return

    cols = st.columns(len(selected))
    for col, name in zip(cols, selected):
        row = df[df["candidate_name"] == name].iloc[0]
        with col:
            with st.container(border=True):
                st.markdown(f"### {name}")
                st.metric("Score", row["score"])
                rec = row["recommendation"]
                color = {"Hire": "green", "Interview": "orange", "Reject": "red"}.get(rec, "gray")
                st.markdown(f"**Recommendation:** :{color}[{rec}]")
                st.markdown(f"**Education:** {row.get('education', 'N/A')}")
                st.markdown(f"**Experience:** {row.get('experience_years', 0)} years")

                st.markdown("**Matching Skills:**")
                for s in row.get("matching_skills", []) or []:
                    st.markdown(f"- {s}")

                st.markdown("**Missing Skills:**")
                for s in row.get("missing_skills", []) or []:
                    st.markdown(f"- :red[{s}]")

                st.markdown("**Extra Skills:**")
                for s in row.get("extra_skills", []) or []:
                    st.markdown(f"- :blue[{s}]")


def _render_expanders(df: pd.DataFrame):
    for _, row in df.iterrows():
        name = row["candidate_name"]
        score = row["score"]
        rec = row["recommendation"]

        with st.expander(f"{name} — Score: {score} | {rec}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Summary**")
                st.write(row.get("summary", "N/A"))
                st.markdown("**Education**")
                st.write(row.get("education", "N/A"))
                st.markdown("**Experience**")
                st.write(f"{row.get('experience_years', 0)} years")

            with col2:
                st.markdown("**Matching Skills**")
                st.write(", ".join(row.get("matching_skills", []) or []))
                st.markdown("**Missing Skills**")
                st.write(", ".join(row.get("missing_skills", []) or []))
                st.markdown("**Extra Skills**")
                st.write(", ".join(row.get("extra_skills", []) or []))

            st.markdown("**Justification**")
            st.write(row.get("justification", "N/A"))

            technical = row.get("technical_questions", []) or []
            hr = row.get("hr_questions", []) or []
            if technical or hr:
                st.markdown("---")
                if technical:
                    st.markdown("**Technical Interview Questions**")
                    for i, q in enumerate(technical, 1):
                        st.markdown(f"{i}. {q}")
                if hr:
                    st.markdown("**HR / Behavioral Questions**")
                    for i, q in enumerate(hr, 1):
                        st.markdown(f"{i}. {q}")
