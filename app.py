import time
import html
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

with st.sidebar:
    st.markdown("### Career Copilot\n**LAB / TEAM NO AI**")
    st.caption("Python skill verification & adaptive practice")
    st.divider()
    page = st.radio("Workspace", ["My profile", "Overview", "Practice", "My skills & CV", "Learning roadmap", "Job Match Analyzer", "History"], key="page")
    st.divider()
    st.write(user["name"])
    st.caption("Private account history · stored on this device")
    if st.button("Sign out", width="stretch"):
        st.session_state.clear()
        st.rerun()



if page == "Overview":
    render_overview(user, history, profile)
elif page == "Practice":
    render_practice(uid, history, profile)
elif page == "My profile":
    render_profile(uid, user, history, profile)
elif page == "My skills & CV":
    render_skills_cv(uid, history, profile)
elif page == "Learning roadmap":
    render_roadmap(history, profile)
elif page == "Job Match Analyzer":
    render_job_analyzer(uid, profile)
elif page == "History":
    render_history(uid, history)
