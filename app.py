"""Career Copilot Lab - Main Application Entrypoint."""

import time
import streamlit as st

from core import storage
from ui.theme import apply_theme
from ui.pages import (
    render_landing_page,
    render_overview,
    render_practice,
    render_skills_cv,
    render_roadmap,
    render_history,
    render_model_lab,
    render_runner_help,
)

st.set_page_config(page_title="Career Copilot Lab", page_icon="🎓", layout="wide")
apply_theme()
storage.init_db()


if "user" not in st.session_state:
    render_landing_page()
    st.stop()

if time.time() - st.session_state.get("last_active", 0) > 1800:
    st.session_state.clear()
    st.rerun()

st.session_state.last_active = time.time()
user = st.session_state.user
uid = user["id"]
history = storage.attempts(uid)
profile = storage.profile(uid)

if "pending_page" in st.session_state:
    st.session_state.page = st.session_state.pop("pending_page")
if "pending_task" in st.session_state:
    st.session_state.task_select = st.session_state.pop("pending_task")

with st.sidebar:
    st.markdown("### Career Copilot\n**LAB / TEAM NO AI**")
    st.caption("Python skill verification & adaptive practice")
    st.divider()
    page = st.radio(
        "Workspace",
        ["Overview", "Practice", "My skills & CV", "Learning roadmap", "History", "Model lab", "Runner help"],
        key="page",
    )
    st.divider()
    st.write(user["name"])
    st.caption("Private account history · stored on this device")
    if st.button("Sign out", width="stretch"):
        st.session_state.clear()
        st.rerun()


def go_to_task(task_id: str) -> None:
    st.session_state.pending_task = task_id
    st.session_state.pending_page = "Practice"
    st.rerun()


if page == "Overview":
    render_overview(user, history, profile, go_to_task)
elif page == "Practice":
    render_practice(user, history, profile, go_to_task)
elif page == "My skills & CV":
    render_skills_cv(user, history, profile)
elif page == "Learning roadmap":
    render_roadmap(user, history, profile, go_to_task)
elif page == "History":
    render_history(user, history)
elif page == "Model lab":
    render_model_lab()
elif page == "Runner help":
    render_runner_help()
