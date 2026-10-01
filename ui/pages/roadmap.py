import pandas as pd
import streamlit as st
from core.adaptive import roadmap, recommend
from ui.components import go_to_task

def render_roadmap(history, profile):
    st.caption("A PLAN BASED ON YOUR ATTEMPTS")
    st.title("Learning roadmap")
    st.write(f"**Goal:** {profile['target']}")
    st.caption("These are educator-authored practice targets, not scraped job requirements or an ML hiring score. Career fit is outside this prototype.")
    st.dataframe(pd.DataFrame(roadmap(history, profile["target"])), hide_index=True, width="stretch")
    next_task, reason = recommend(history, profile["target"])
    st.info(reason)
    if st.button(f"Practise: {next_task['title']}", type="primary"):
        go_to_task(next_task["id"])
    st.subheader("Practice project suggestions")
    st.caption("Project briefs for extra learning. These are not automatically graded by the runner.")
    projects_by_goal = {
        "Python foundations": [
            ("Student result calculator", "Conditions + Functions", "Create functions for total, average and grade. Test exact grade boundaries and an empty mark list."),
            ("Daily expense summary", "Loops + Lists", "Total expenses, find the largest amount and remove duplicates. Test empty and single-item inputs."),
            ("Number practice toolkit", "Functions + Loops", "Combine prime checking, digit sum and GCD functions. Write a test table and explain failures."),
        ],
        "Python backend preparation": [
            ("Request validator", "Conditions + Functions", "Validate method, path and required fields for a small request dictionary."),
            ("Account rules", "Loops + Conditions", "Check password rules and locate a matching username without exposing stored passwords."),
            ("Batch input cleaner", "Lists + Functions", "Normalize a list of submitted values and reject invalid records before a mock insert."),
        ],
        "Data analysis foundations": [
            ("Tabular data cleaner", "Lists + Loops", "Clean rows, handle missing values and convert numeric text while recording rejected rows."),
            ("Summary statistics", "Functions + Lists", "Implement mean and median with explicit empty-input behaviour and boundary tests."),
            ("Category frequency report", "Loops + Conditions", "Count categories from records and return a deterministic, sorted summary."),
        ],
    }
    for title, topics, brief in projects_by_goal[profile["target"]]:
        with st.expander(title + " / " + topics):
            st.write(brief)
