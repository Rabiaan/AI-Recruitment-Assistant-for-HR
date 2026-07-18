import pandas as pd
import streamlit as st


def render_ranking(results):
    if not results:
        st.info("No results to display yet.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)

    st.subheader("Candidate Ranking")

    def color_recommendation(val):
        colors = {
            "Hire": "background-color: #d4edda; color: #155724;",
            "Interview": "background-color: #fff3cd; color: #856404;",
            "Reject": "background-color: #f8d7da; color: #721c24;",
        }
        return colors.get(val, "")

    styled_df = df[["name", "score", "recommendation", "justification"]].style.apply(
        lambda row: [color_recommendation(row["recommendation"]) if col == "recommendation" else "" for col in row.index],
        axis=1,
    )
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    selected = st.multiselect(
        "Compare candidates (select 2-3)",
        options=df["name"].tolist(),
        default=[],
        max_selections=3,
        key="compare_candidates",
    )

    if len(selected) >= 2:
        st.subheader("Candidate Comparison")
        cols = st.columns(len(selected))
        for col, name in zip(cols, selected):
            candidate = df[df["name"] == name].iloc[0]
            with col:
                with st.container(border=True):
                    st.markdown(f"### {name}")
                    st.metric("Score", candidate["score"])
                    st.markdown(f"**Recommendation:** {candidate['recommendation']}")
                    st.markdown(f"**Matching Skills:** {', '.join(candidate['matching_skills'])}")
                    st.markdown(f"**Missing Skills:** {', '.join(candidate['missing_skills'])}")
                    st.markdown(f"**Summary:** {candidate['summary']}")

    for idx, row in df.iterrows():
        with st.expander(f"#{idx + 1} — {row['name']} (Score: {row['score']})"):
            st.write(f"**Summary:** {row['summary']}")
            st.write(f"**Matching Skills:** {', '.join(row['matching_skills'])}")
            st.write(f"**Missing Skills:** {', '.join(row['missing_skills'])}")
            st.write(f"**Extra Skills:** {', '.join(row['extra_skills'])}")
            st.write(f"**Recommendation:** {row['recommendation']}")
            st.write(f"**Justification:** {row['justification']}")
            questions = row.get("interview_questions", {})
            if questions:
                st.write("**Interview Questions:**")
                for category, qs in questions.items():
                    st.write(f"- {category}:")
                    for q in qs:
                        st.write(f"  - {q}")
