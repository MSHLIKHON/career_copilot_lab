import time
import streamlit as st
from core import storage
from core.model import load_metrics, MODEL_DIR

def authenticate():
    st.markdown('<div class="eyebrow">TEAM NO AI · CAREER SKILLS PRACTICE LAB</div>', unsafe_allow_html=True)
    st.title("Career Copilot Lab")
    st.write("Show what you can do. Learn from each attempt.")
    story, account = st.columns([1.15, .85], gap="large")
    with story:
        st.markdown('<div class="intro"><h2>Practice with a next step.</h2><p>Build Python evidence, understand each mistake and follow a roadmap shaped by your work.</p></div>', unsafe_allow_html=True)
        st.markdown('''<div class="feature-grid">
<div class="feature-card"><b>20 focused tasks</b>Conditions, loops, functions and lists.</div>
<div class="feature-card"><b>Private progress</b>Assisted and independent evidence stays separate.</div>
<div class="feature-card"><b>Career preparation</b>Saved CV, skill gaps and learning roadmaps.</div>
</div>''', unsafe_allow_html=True)
        st.info("Local classroom prototype · Private on this computer · No API key required")

    with account:
        st.markdown('<div class="auth-heading">Your learning workspace</div>'
                    '<p class="auth-subheading">Sign in or create a private local account.</p>',
                    unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])
        with login_tab:
            st.markdown('<div class="auth-heading">Welcome back</div>'
                        '<p class="auth-subheading">Sign in to continue your practice.</p>',
                        unsafe_allow_html=True)
            with st.form("login"):
                username = st.text_input("Username", max_chars=24)
                password = st.text_input("Password", type="password", max_chars=128)
                submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
            if submitted:
                try:
                    user = storage.login(username, password)
                    if user:
                        st.session_state.clear()
                        st.session_state.user = user
                        st.session_state.last_active = time.time()
                        st.rerun()
                    st.error("Username or password is incorrect.")
                except ValueError as error:
                    st.error(str(error))
        with register_tab:
            with st.form("register"):
                name = st.text_input("Your name", placeholder="Your display name", max_chars=80)
                username = st.text_input("Choose username", placeholder="3–24 letters, numbers or _", max_chars=24)
                email = st.text_input("Email address", placeholder="you@example.com", max_chars=254)
                phone = st.text_input("Phone number", placeholder="+880 1XXX-XXXXXX", max_chars=24)
                password = st.text_input("Choose password", type="password", placeholder="8–128 characters", max_chars=128)
                confirm = st.text_input("Confirm password", type="password", placeholder="Repeat password", max_chars=128)
                consent = st.checkbox("Save my progress on this computer")
                form_message = st.empty()
                submitted = st.form_submit_button("Create account and start", type="primary", width="stretch")
            if submitted:
                if password != confirm:
                    form_message.error("Passwords do not match. Re-enter the same password in both fields.")
                elif not consent:
                    form_message.error("Please allow local storage to save your practice and profile.")
                else:
                    try:
                        if not email.strip() or not phone.strip():
                            raise ValueError("Email address and phone number are required.")
                        storage.register(username, name, password, email, phone)
                        user = storage.login(username, password)
                        st.session_state.clear()
                        st.session_state.user = user
                        st.session_state.last_active = time.time()
                        st.rerun()
                    except ValueError as error:
                        if "already taken" in str(error):
                            form_message.error("This username is already taken. Try adding a few numbers or choose another name.")
                        else:
                            form_message.error(str(error))

    st.divider()
    st.caption("TECHNICAL NOTES · OPTIONAL READING")
    model_col, runner_col = st.columns(2, gap="large")
    with model_col:
        with st.expander("Model evidence and limitations"):
            st.write("The local pilot classifier suggests one of four likely programming-mistake categories.")
            metrics, metrics_error = load_metrics()
            if metrics_error:
                st.warning(metrics_error)
            else:
                st.warning(metrics["warning"])
                st.write("**Approach:** Character TF-IDF + Logistic Regression; Linear SVM is a comparison baseline.")
                for name, values in metrics["models"].items():
                    test_metrics = values["test"]
                    st.write(f"**{name.replace('_', ' ').title()}**  ·  "
                             f"Accuracy {test_metrics['accuracy']:.1%}  ·  "
                             f"Macro F1 {test_metrics['macro_f1']:.1%}")
                st.download_button("Download evaluation report", (MODEL_DIR / "metrics.json").read_bytes(),
                                   "evaluation_metrics.json", "application/json")
    with runner_col:
        with st.expander("Safe runner rules and supported Python"):
            st.write("Submitted code runs in a restricted AST interpreter; the app never calls eval or exec on it.")
            st.markdown("""
**Supported:** positional functions, return, conditions, loops, assignment, basic
arithmetic, comparisons, lists, tuples, strings, indexing and slicing.

**Allowed functions:** len, range, sum, min, max, abs, sorted, reversed, list, int,
str, bool, enumerate and round.

**Not supported:** imports, attributes/methods, files, network, input, print, classes,
dictionaries, sets, comprehensions, lambda, generators, decorators or top-level calls.
""")
