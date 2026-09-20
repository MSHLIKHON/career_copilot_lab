"""Learning roadmap and practice project suggestions page."""

import pandas as pd
import streamlit as st

from core.adaptive import roadmap, recommend


def render_roadmap(user: dict, history: list, profile: dict, go_to_task_cb) -> None:
    st.caption("A PLAN BASED ON YOUR ATTEMPTS")
    st.title("Learning roadmap")
    st.write(f"**Goal:** {profile['target']}")
    st.caption(
        "These are educator-authored practice targets, not scraped job requirements or an ML hiring score. "
        "Career fit is outside this prototype."
    )
    st.dataframe(pd.DataFrame(roadmap(history, profile["target"])), hide_index=True, width="stretch")
    next_task, reason = recommend(history, profile["target"])
    st.info(reason)
    if st.button(f"Practise: {next_task['title']}", type="primary"):
        go_to_task_cb(next_task["id"])
    st.subheader("Practice project suggestions")
    st.caption("Project briefs for extra learning. These are not automatically graded by the runner.")
    for title, topics, brief in [
        (
            "Student result calculator",
            "Conditions + Functions",
            "Create functions for total, average and grade. Test the exact grade boundaries and an empty mark list.",
        ),
        (
            "Daily expense summary",
            "Loops + Lists",
            "Write functions to total expenses, find the largest amount and remove duplicates. Test empty and single-item inputs.",
        ),
        (
            "Number practice toolkit",
            "Functions + Loops",
            "Combine prime checking, digit sum and GCD functions. Write your own test table and explain failed cases.",
        ),
    ]:
        with st.expander(title + " / " + topics):
            st.write(brief)
