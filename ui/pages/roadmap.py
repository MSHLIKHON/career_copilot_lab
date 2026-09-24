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
    projects_by_goal = {
        "Python foundations": [
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
        ],
        "Python backend preparation": [
            (
                "Simple REST API Mock",
                "Functions + Conditions",
                "Create functions that mock handling HTTP requests, returning JSON-like dictionary responses.",
            ),
            (
                "User Authentication System",
                "Loops + Conditions",
                "Write functions to check password strength and validate a login against a list of stored credentials.",
            ),
            (
                "Request Data Validator",
                "Lists + Functions",
                "Build a function that takes a list of raw inputs and cleans or validates them for a mock database insert.",
            ),
        ],
        "Data analysis foundations": [
            (
                "CSV Data Cleaner",
                "Lists + Loops",
                "Write a function that iterates through a list of rows, removing empty values and parsing strings to floats.",
            ),
            (
                "Summary Statistics Calculator",
                "Functions + Lists",
                "Build functions to calculate the mean, median, and mode from a raw list of numerical data.",
            ),
            (
                "Category Data Grouper",
                "Loops + Conditions",
                "Create a script that takes a list of record dictionaries and groups them by a specific category key.",
            ),
        ]
    }
    
    projects = projects_by_goal.get(profile["target"], projects_by_goal["Python foundations"])
    
    for title, topics, brief in projects:
        with st.expander(title + " / " + topics):
            st.write(brief)
