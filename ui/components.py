"""Small reusable landing-page components (solid colors only, no gradients)."""

import streamlit as st


def eyebrow(text: str) -> None:
    st.markdown(f'<div class="hero-eyebrow">{text}</div>', unsafe_allow_html=True)


def hero_headline(text: str) -> None:
    st.markdown(f'<div class="hero-title">{text}</div>', unsafe_allow_html=True)


def hero_sub(text: str) -> None:
    st.markdown(f'<div class="hero-sub">{text}</div>', unsafe_allow_html=True)


def feature_card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="feature-card"><h4>{title}</h4><p>{body}</p></div>',
        unsafe_allow_html=True,
    )


def prototype_notice() -> None:
    st.markdown(
        '<div class="prototype-note">Local classroom prototype — '
        'your account and attempts are stored on this computer only.</div>',
        unsafe_allow_html=True,
    )
