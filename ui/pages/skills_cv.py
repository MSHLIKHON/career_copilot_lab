"""My skills & CV claims / parsing page."""

import io
import pandas as pd
import streamlit as st
from pypdf import PdfReader

from core import storage
from core.adaptive import SKILLS, GOALS, extract_claims, summarize


def render_skills_cv(user: dict, history: list, profile: dict) -> None:
    uid = user["id"]
    st.caption("CLAIMS AND EVIDENCE")
    st.title("My skills & CV")
    st.write("Paste CV text or upload a text-based PDF/TXT. Review the extracted keywords before saving.")
    st.caption(
        "The parser recognises listed skill words, not proficiency, context or negation. "
        "SQL/React and other non-Python skills remain unassessed."
    )
    cv_text = st.text_area("CV text (optional)", max_chars=50000, height=120)
    uploaded = st.file_uploader("CV file (optional; maximum 2 MB)", type=["pdf", "txt"])
    if st.button("Extract skill keywords"):
        try:
            text = cv_text
            if uploaded:
                if uploaded.size > 2 * 1024 * 1024:
                    raise ValueError("File must be at most 2 MB.")
                if uploaded.name.lower().endswith(".pdf"):
                    reader = PdfReader(io.BytesIO(uploaded.getvalue()))
                    if reader.is_encrypted:
                        raise ValueError("Use an unencrypted PDF.")
                    if len(reader.pages) > 10:
                        raise ValueError("Use a CV with at most 10 pages.")
                    text += "\n" + "\n".join((p.extract_text() or "")[:10000] for p in reader.pages)
                else:
                    text += "\n" + uploaded.getvalue().decode("utf-8")
            found = extract_claims(text)
            st.session_state.claim_choices = found
            if found:
                st.success("Keywords extracted. Review the selected claims, then save.")
            else:
                st.warning("No supported keywords found. Scanned PDFs need OCR; select skills manually below.")
        except Exception as error:
            st.error(f"Could not read CV: {error}")
    if "claim_choices" not in st.session_state:
        st.session_state.claim_choices = profile["claims"]
    claims = st.multiselect("Skills you claim (confirm manually)", SKILLS, key="claim_choices")
    target = st.selectbox("Learning goal", list(GOALS), index=list(GOALS).index(profile["target"]))
    if st.button("Save skill profile", type="primary"):
        storage.save_profile(uid, claims, target)
        st.success("Profile saved. Raw CV text/file is not written to the database.")
    st.subheader("Claimed vs assessed")
    rows = []
    for skill in claims:
        rows.append(
            {
                "Skill": skill,
                "Claim": "Claimed by learner",
                "Evidence": (
                    f"{len(history)} Python attempts recorded; see topic results"
                    if skill == "Python" and history
                    else "Not assessed"
                ),
            }
        )
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("Add at least one skill claim to see its assessment status.")
    summary_df = pd.DataFrame(summarize(history))
    if "Highest evidenced level" in summary_df.columns:
        summary_df = summary_df.drop(columns=["Highest evidenced level"])
    st.dataframe(summary_df, hide_index=True, width="stretch")
