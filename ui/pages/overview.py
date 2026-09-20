"""Overview / Dashboard workspace page."""

import pandas as pd
import streamlit as st

from core.adaptive import recommend, summarize


def render_overview(user: dict, history: list, profile: dict, go_to_task_cb) -> None:
    st.caption("YOUR LEARNING WORKSPACE")
    st.title(f"Welcome, {user['name']}")
    st.write("Test a skill. Understand a mistake. Choose your next step.")
    done = {a["task_id"] for a in history if a["result"]["status"] == "passed"}
    independent = {
        a["task_id"]
        for a in history
        if a["result"]["status"] == "passed"
        and not a["hints"]
        and not a["solution_seen"]
    }
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ["Attempts", "Tasks passed", "Independent passes", "Available tasks"],
        [len(history), len(done), len(independent), 20],
    ):
        col.metric(label, value)
    st.progress(len(done) / 20, text=f"{len(done)} of 20 tasks have a passing attempt")
    st.subheader("Your next task")
    next_task, reason = recommend(history, profile["target"])
    st.write(f"**{next_task['title']}** · {next_task['topic']} · Level {next_task['level']}")
    st.write(reason)
    if st.button("Start recommended task", type="primary"):
        go_to_task_cb(next_task["id"])
    st.subheader("Evidence by topic")
    st.dataframe(pd.DataFrame(summarize(history)), hide_index=True, width="stretch")
    st.caption("A passing task is limited evidence, not a certificate of expertise or job readiness.")
