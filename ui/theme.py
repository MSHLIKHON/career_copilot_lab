"""Shared Streamlit theme CSS (no gradients).

Restrained palette derived from `.streamlit/config.toml`:
- primary accent: #3B64F4
- background:    #F7F9FC
- surface:       #FFFFFF
- text:          #17243D
- border:        #E5EAF4
- muted text:    #5A6B8C
"""

import streamlit as st


def apply_theme() -> None:
    """Inject the global + landing-page CSS. Safe to call once per run."""
    st.markdown(
        """<style>
/* Remove full-page artificial margins and make full screen */
.stApp {margin:0 !important;padding:0 !important}
[data-testid="stAppViewContainer"] {padding:0 !important}
.block-container {
    max-width:100% !important;
    width:100% !important;
    padding-top:1.25rem !important;
    padding-bottom:3rem !important;
    padding-left:3rem !important;
    padding-right:3rem !important;
}

h1,h2,h3 {letter-spacing:-.035em}
[data-testid="stSidebar"] {border-right:1px solid #E5EAF4}
[data-testid="stMetric"] {background:white;border:1px solid #E5EAF4;border-radius:14px;padding:18px}
.intro {background:#182849;color:#fff;padding:28px 32px;border-radius:18px;margin-bottom:24px}
.intro h2 {color:#fff;margin:0 0 8px}.intro p {margin:0;color:#d8e2fb}
.eyebrow {font-size:12px;letter-spacing:.12em;color:#6684c6;font-weight:700}

/* Hide Streamlit header & toolbar entirely */
header[data-testid="stHeader"],
.stAppHeader,
[data-testid="stToolbar"],
.stAppToolbar,
.stAppDeployButton,
#MainMenu,
footer {
    display:none !important;
    height:0 !important;
    min-height:0 !important;
    padding:0 !important;
    margin:0 !important;
}

/* Landing page Top Navbar */
.landing-navbar {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding-bottom:1rem;
    border-bottom:1px solid #E5EAF4;
    margin-bottom:1.5rem;
}
.landing-nav-brand-box {
    display:flex;
    flex-direction:column;
}
.landing-nav-brand {
    font-weight:800;
    font-size:18px;
    color:#17243D;
    letter-spacing:-.02em;
}
.landing-nav-sub {
    font-size:12.5px;
    color:#5A6B8C;
}
.landing-nav-menu {
    display:flex;
    align-items:center;
    gap:1.75rem;
}
.landing-nav-item {
    font-size:15px;
    font-weight:600;
    color:#17243D;
    text-decoration:none !important;
    padding:6px 4px;
    cursor:pointer;
    transition:color 0.15s ease;
}
.landing-nav-item:hover {
    text-decoration:underline !important;
    color:#3B64F4;
}

/* Landing page content */
.hero-eyebrow {font-size:12px;letter-spacing:.12em;color:#3B64F4;font-weight:700;margin:18px 0 10px}
.hero-title {font-size:clamp(30px,4.5vw,46px);line-height:1.08;letter-spacing:-.04em;color:#17243D;margin:0 0 12px;font-weight:800}
.hero-sub {font-size:16px;line-height:1.6;color:#3E4F6E;max-width:720px;margin:0 0 20px}
.feature-card {background:#FFFFFF;border:1px solid #E5EAF4;border-radius:14px;padding:18px 18px;min-height:132px}
.feature-card h4 {margin:0 0 6px;font-size:15px;color:#17243D;letter-spacing:-.01em}
.feature-card p {margin:0;font-size:13.5px;line-height:1.55;color:#3E4F6E}
.landing-section-title {font-size:20px;font-weight:750;color:#17243D;letter-spacing:-.02em;margin:6px 0 4px}
.landing-section-sub {font-size:14px;color:#5A6B8C;margin:0 0 14px}
.auth-panel {background:#FFFFFF;border:1px solid #E5EAF4;border-radius:16px;padding:8px 20px 16px}
</style>""",
        unsafe_allow_html=True,
    )
