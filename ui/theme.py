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
.block-container {max-width:1160px;padding-top:1.5rem;padding-bottom:3rem}
h1,h2,h3 {letter-spacing:-.035em}
[data-testid="stSidebar"] {border-right:1px solid #E5EAF4}
[data-testid="stMetric"] {background:white;border:1px solid #E5EAF4;border-radius:14px;padding:18px}
.intro {background:#182849;color:#fff;padding:28px 32px;border-radius:18px;margin-bottom:24px}
.intro h2 {color:#fff;margin:0 0 8px}.intro p {margin:0;color:#d8e2fb}
.eyebrow {font-size:12px;letter-spacing:.12em;color:#6684c6;font-weight:700}
/* Hide Streamlit toolbar */
[data-testid="stToolbar"],
.stAppToolbar {display:none !important}
/* Landing page */
.landing-nav-brand {font-weight:800;font-size:17px;color:#17243D;letter-spacing:-.02em;padding-top:.55rem}
.landing-nav-sub {font-size:12px;color:#5A6B8C;margin-top:-6px}
.landing-nav-link {font-size:14px;font-weight:600;color:#3B64F4;text-decoration:none;padding:.55rem 0;display:inline-block}
.landing-nav-link:hover {text-decoration:underline}
.hero-eyebrow {font-size:12px;letter-spacing:.12em;color:#3B64F4;font-weight:700;margin:18px 0 10px}
.hero-title {font-size:clamp(30px,4.5vw,46px);line-height:1.08;letter-spacing:-.04em;color:#17243D;margin:0 0 12px;font-weight:800}
.hero-sub {font-size:16px;line-height:1.6;color:#3E4F6E;max-width:640px;margin:0 0 20px}
.feature-card {background:#FFFFFF;border:1px solid #E5EAF4;border-radius:14px;padding:18px 18px;min-height:132px}
.feature-card h4 {margin:0 0 6px;font-size:15px;color:#17243D;letter-spacing:-.01em}
.feature-card p {margin:0;font-size:13.5px;line-height:1.55;color:#3E4F6E}
.landing-section-title {font-size:20px;font-weight:750;color:#17243D;letter-spacing:-.02em;margin:6px 0 4px}
.landing-section-sub {font-size:14px;color:#5A6B8C;margin:0 0 14px}
.auth-panel {background:#FFFFFF;border:1px solid #E5EAF4;border-radius:16px;padding:8px 20px 16px}
</style>""",
        unsafe_allow_html=True,
    )
