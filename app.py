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
    render_job_analyzer,
)

PAGES = [
    "Overview",
    "Practice",
    "My skills & CV",
    "Learning roadmap",
    "Job Match Analyzer",
    "History",
]

st.set_page_config(
    page_title="Career Copilot Lab",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()
storage.init_db()

# Auto-restore session from the query parameter on page refresh
if "user" not in st.session_state:
    token = st.query_params.get("token")
    if token:
        restored_user = storage.get_user_by_session(token)
        if restored_user:
            st.session_state.user = restored_user
            st.session_state.session_token = token
            st.session_state.last_active = time.time()
        else:
            # Expired or invalid token: drop it from the URL
            st.query_params.clear()

if "user" not in st.session_state:
    render_landing_page()
    st.stop()

# Inactivity timeout (30 minutes)
if time.time() - st.session_state.get("last_active", 0) > 1800:
    token = st.session_state.get("session_token") or st.query_params.get("token")
    if token:
        storage.delete_session(token)
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

st.session_state.last_active = time.time()
user = st.session_state.user
uid = user["id"]
history = storage.attempts(uid)
profile = storage.profile(uid)

# Apply navigation requests made by buttons on other pages
if "pending_page" in st.session_state:
    st.session_state.page = st.session_state.pop("pending_page")
if "pending_task" in st.session_state:
    st.session_state.task_select = st.session_state.pop("pending_task")

# Guard against a stale page value (e.g. a removed menu item)
if "page" not in st.session_state:
    url_page = st.query_params.get("page")
    if url_page and url_page in PAGES:
        st.session_state.page = url_page
    else:
        st.session_state.page = PAGES[0]
elif st.session_state.page not in PAGES:
    st.session_state.page = PAGES[0]

with st.sidebar:
    st.markdown("### Career Copilot\n**LAB / TEAM NO AI**")
    st.caption("Python skill verification & adaptive practice")
    st.divider()
    page = st.radio("Workspace", PAGES, key="page")
    st.query_params["page"] = page
    st.divider()
    st.write(user["name"])
    st.caption("Private account history · stored on this device")
    if st.button("Sign out", width="stretch"):
        token = st.session_state.get("session_token") or st.query_params.get("token")
        if token:
            storage.delete_session(token)
        st.session_state.clear()
        st.query_params.clear()
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
elif page == "Job Match Analyzer":
    render_job_analyzer(user, history, profile)
elif page == "History":
    render_history(user, history)