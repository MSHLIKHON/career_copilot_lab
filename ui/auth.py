"""Authentication UI (login / signup forms).

Task 1 scope: extracted unchanged from the old `app.py::authenticate()`
(top title/hero intentionally lives in `ui/pages/landing.py` so there is
exactly one `st.title("Career Copilot Lab")` on the public page).

Task 2 will redesign these forms. Widget labels, form names and keys are
frozen because `tests/test_app.py` drives them directly:
- "Your name", "Choose username", "Choose password", "Confirm password",
  "Create account", checkbox[0]
- "Username", "Password", "Sign in"
"""

import time

import streamlit as st

from core import storage


def render_auth_forms() -> None:
    """Render the sign-in / create-account panels and handle submissions."""
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(
            '<div class="intro"><h2>Practice with a next step.</h2>'
            "<p>Small Python challenges, real test evidence and hints "
            "that help you move forward.</p></div>",
            unsafe_allow_html=True,
        )
        st.write("**20 tasks** across Conditions, Loops, Functions and Lists.")
        st.write("**Your own progress** saved locally, with assisted and independent attempts separated.")
        st.write("**A trained pilot model** suggests mistake categories. Predictions can be wrong.")
    with right:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])
        with login_tab:
            with st.form("login"):
                username = st.text_input("Username", max_chars=24)
                password = st.text_input("Password", type="password", max_chars=128)
                submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
            if submitted:
                try:
                    user = storage.login(username, password)
                    if user:
                        token = storage.create_session(user["id"])
                        st.query_params["token"] = token
                        st.session_state.clear()
                        st.session_state.user = user
                        st.session_state.session_token = token
                        st.session_state.last_active = time.time()
                        st.rerun()
                    st.error("Username or password is incorrect.")
                except ValueError as error:
                    st.error(str(error))
        with register_tab:
            with st.form("register"):
                name = st.text_input("Your name", max_chars=80)
                username = st.text_input(
                    "Choose username",
                    help="3-24 letters, digits or underscores",
                    max_chars=24,
                )
                password = st.text_input("Choose password", type="password", max_chars=128)
                confirm = st.text_input("Confirm password", type="password", max_chars=128)
                consent = st.checkbox("I understand my attempts and profile will be stored on this computer.")
                submitted = st.form_submit_button("Create account", width="stretch")
            if submitted:
                if password != confirm:
                    st.error("Passwords do not match.")
                elif not consent:
                    st.error("Please confirm local storage consent.")
                else:
                    try:
                        storage.register(username, name, password)
                        st.success("Account created. Open Sign in and use your new username and password.")
                    except ValueError as error:
                        st.error(str(error))
        st.markdown("</div>", unsafe_allow_html=True)
