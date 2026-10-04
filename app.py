import time
import streamlit as st
from core import storage
from ui.theme import apply_theme
from ui.auth import authenticate
from ui.pages.overview import render_overview
from ui.pages.practice import render_practice
from ui.pages.profile import render_profile
from ui.pages.skills_cv import render_skills_cv
from ui.pages.roadmap import render_roadmap
from ui.pages.job_analyzer import render_job_analyzer
from ui.pages.history import render_history

st.set_page_config(page_title="Career Copilot Lab", layout="wide")
apply_theme()
storage.init_db()

if "user" not in st.session_state:
    authenticate()
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

PAGES = {
    "My profile": lambda: render_profile(uid, user, history, profile),
    "Overview": lambda: render_overview(user, history, profile),
    "Practice": lambda: render_practice(uid, history, profile),
    "My skills & CV": lambda: render_skills_cv(uid, history, profile),
    "Learning roadmap": lambda: render_roadmap(history, profile),
    "Job Match Analyzer": lambda: render_job_analyzer(uid, profile),
    "History": lambda: render_history(uid, history),
}

with st.sidebar:
    st.markdown("### Career Copilot\n**LAB / TEAM NO AI**")
    st.caption("Python skill verification & adaptive practice")
    st.divider()
    page = st.radio("Workspace", list(PAGES.keys()), key="page")
    st.divider()
    st.write(user["name"])
    st.caption("Private account history · stored on this device")
    if st.button("Sign out", width="stretch"):
        st.session_state.clear()
        st.rerun()

render_page = PAGES.get(page)
if render_page:
    render_page()
