import streamlit as st

from ui.auth import render_auth_forms
from ui.components import eyebrow, feature_card, hero_headline, hero_sub

LANDING_VIEW_KEY = "landing_view"


def _set_view(view: str) -> None:
    st.session_state[LANDING_VIEW_KEY] = view
    st.rerun()


def render_nav() -> None:
    st.markdown(
        """
        <div class="landing-navbar">
            <div class="landing-nav-brand-box">
                <div class="landing-nav-brand">🎓 Career Copilot Lab</div>
                <div class="landing-nav-sub">Python skill verification &amp; adaptive practice</div>
            </div>
            <div class="landing-nav-menu">
                <a class="landing-nav-item" href="#login-section" onclick="switchAuthTab(0)">Login</a>
                <a class="landing-nav-item" href="#signup-section" onclick="switchAuthTab(1)">Sign Up</a>
            </div>
        </div>
        <script>
        function switchAuthTab(index) {
            try {
                const doc = window.parent.document || document;
                const tabs = doc.querySelectorAll('button[data-testid="stTab"]');
                if (tabs && tabs[index]) {
                    tabs[index].click();
                }
            } catch(e) {}
        }
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    eyebrow("TEAM NO AI · AI SKILL VERIFICATION & ADAPTIVE PRACTICE")
    hero_headline("Build skills. Prove them. Know what to practice next.")
    hero_sub(
        "Career Copilot Lab helps students practice Python with small tasks, "
        "understand mistakes through feedback, keep evidence of progress, "
        "and follow adaptive recommendations on what to practice next."
    )
    cta_primary, cta_secondary, _ = st.columns([0.9, 1.1, 2.2])
    with cta_primary:
        # Task 2: scroll/focus the redesigned signup form.
        if st.button("Start Practicing", key="hero_start", type="primary", width="stretch"):
            _set_view("auth-signup")
    with cta_secondary:
        if st.button("See How It Works", key="hero_how", width="stretch"):
            _set_view("how-it-works")


def render_features() -> None:
    st.markdown(
        '<div class="landing-section-title">What you get</div>'
        '<div class="landing-section-sub">A focused practice loop: attempt, feedback, evidence, next step.</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    features = [
        ("Practical Python skill tests", "20 small tasks across conditions, loops, functions and lists with deterministic tests."),
        ("AI-powered mistake feedback", "A trained pilot classifier suggests likely mistake categories alongside exact test results."),
        ("Adaptive practice", "Recommendations point to the next task at the right level based on your attempts and goal."),
        ("Progress and skill evidence", "Attempts, hints and independent passes are saved locally and summarised by topic."),
    ]
    for col, (title, body) in zip(cols, features):
        with col:
            feature_card(title, body)


def render_context_section(view: str) -> None:
    """Render the How-it-works panel selected via hero CTAs."""
    if view == "how-it-works":
        st.divider()
        st.subheader("How it works")
        st.write(
            "1. Create an account and attempt a recommended task.  "
            "2. Run the tests to get exact pass/fail evidence plus mistake feedback.  "
            "3. Use hints sparingly — assisted attempts are recorded separately.  "
            "4. Follow the recommended next task or your learning roadmap."
        )
    elif view in ("auth-login", "auth-signup"):
        st.caption(
            "Continue below to sign in or create an account. "
            "Task 2 will connect this selection to a redesigned form."
        )


def render_landing_page() -> None:
    """Entry point called by `app.py` for unauthenticated users."""
    if LANDING_VIEW_KEY not in st.session_state:
        st.session_state[LANDING_VIEW_KEY] = "landing"
    view = st.session_state[LANDING_VIEW_KEY]

    render_nav()
    st.title("Career Copilot Lab")
    st.write("Show what you can do. Learn from each attempt.")
    render_hero()
    st.divider()
    render_features()
    st.divider()
    render_context_section(view)
    st.divider()
    st.markdown(
        '<div id="login-section"></div><div id="signup-section"></div>'
        '<div class="landing-section-title">Sign in or create your account</div>'
        '<div class="landing-section-sub">Your progress stays on this computer. No default password exists.</div>',
        unsafe_allow_html=True,
    )
    render_auth_forms()
