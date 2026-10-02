import time
import streamlit as st
from core import storage
from core.model import load_metrics, MODEL_DIR

def authenticate():
    st.markdown('<div class="eyebrow">CAREER SKILLS PRACTICE LAB · LOCAL WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Career Copilot Lab")
    st.markdown('<p class="hero-subtitle">Demonstrate verified coding proficiency, track evidence-based learning, and align your skills with industry roles.</p>', unsafe_allow_html=True)
    story, account = st.columns([1.12, 0.88], gap="large")
    with story:
        st.markdown('''<div class="intro">
<h2>Practice with verified evidence.</h2>
<p>Build authentic Python code evidence, understand failure modes with automated classification, and match your skills against real-world tech roles.</p>
</div>''', unsafe_allow_html=True)
        st.markdown('''<div class="feature-grid">
<div class="feature-card"><b>20 Verified Tasks</b>Curated Python challenges across conditions, loops, functions, and lists with automated AST safety verification.</div>
<div class="feature-card"><b>Segregated Evidence</b>Assisted hint submissions and independent passes are strictly segregated to prove verified competency.</div>
<div class="feature-card"><b>Job Match & CV Analytics</b>Extract candidate skills from your CV, benchmark against real roles, and follow an adaptive learning roadmap.</div>
</div>''', unsafe_allow_html=True)
        st.markdown('''<div class="privacy-badge">
<span class="privacy-badge-dot"></span>
<span>Local classroom prototype · Private on this computer · No API key required</span>
</div>''', unsafe_allow_html=True)

    with account:
        st.markdown('<div class="auth-heading">Learning Workspace</div>'
                    '<p class="auth-subheading">Sign in to your private workspace or create a local account.</p>',
                    unsafe_allow_html=True)
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

    st.markdown('''<div class="specs-header">
<span class="specs-tag">TECHNICAL ARCHITECTURE</span>
<h4>System Constraints & Model Evaluation</h4>
</div>''', unsafe_allow_html=True)
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
