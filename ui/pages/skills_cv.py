import io
import pandas as pd
import streamlit as st
from pypdf import PdfReader
from core import storage
from core.adaptive import SKILLS, GOALS, extract_claims, summarize
from core.job_ml import KNOWN_SKILLS

def render_skills_cv(uid, history, profile):
    st.caption("CLAIMS AND EVIDENCE")
    st.title("My skills & CV")
    st.write("Paste CV text or upload a text-based PDF/TXT. Review the extracted keywords, then save the CV to your private profile.")
    st.caption("The parser recognises listed skill words, not proficiency, context or negation. SQL/React and other non-Python skills remain unassessed.")
    if "cv_text_draft" not in st.session_state:
        st.session_state.cv_text_draft = profile["cv_text"]
    cv_text = st.text_area("CV text (optional)", max_chars=50000, height=160, key="cv_text_draft",
                           on_change=lambda: st.session_state.pop("extracted_cv_text", None))
    uploaded = st.file_uploader("CV file (optional; maximum 2 MB)", type=["pdf", "txt"])
    if st.button("Extract skill keywords"):
        try:
            text = (cv_text or "").strip()
            if uploaded:
                if uploaded.size > 2 * 1024 * 1024:
                    raise ValueError("File must be at most 2 MB.")
                if uploaded.name.lower().endswith(".pdf"):
                    reader = PdfReader(io.BytesIO(uploaded.getvalue()))
                    if reader.is_encrypted:
                        raise ValueError("Use an unencrypted PDF.")
                    if len(reader.pages) > 10:
                        raise ValueError("Use a CV with at most 10 pages.")
                    extracted = "\n".join((p.extract_text() or "").strip()[:10000] for p in reader.pages)
                    text = f"{text}\n{extracted}".strip()
                else:
                    try:
                        decoded = uploaded.getvalue().decode("utf-8")
                    except UnicodeDecodeError:
                        decoded = uploaded.getvalue().decode("latin-1", errors="replace")
                    text = f"{text}\n{decoded}".strip()
            if not text:
                st.warning("Paste CV text or upload a CV file first.")
            else:
                found = extract_claims(text)
                st.session_state.extracted_cv_text = text[:50000]
                st.session_state.claim_choices = found
                if found:
                    st.success(f"{len(found)} keyword(s) extracted. Review the selected claims, then save.")
                else:
                    st.warning("No supported keywords found. Scanned PDFs need OCR; select skills manually below.")
        except Exception as error:
            st.error(f"Could not read CV: {error}")
    if "claim_choices" not in st.session_state:
        st.session_state.claim_choices = profile["claims"]
        
    all_options = sorted(list(set(SKILLS + [s.title() for s in KNOWN_SKILLS] + st.session_state.claim_choices)))
    claims = st.multiselect("Skills you claim (confirm manually)", all_options, key="claim_choices")
    target = st.selectbox("Learning goal", list(GOALS), index=list(GOALS).index(profile["target"]))
    save_cv = st.checkbox("Save this CV text in my private local profile", value=True)
    if st.button("Save skills & CV", type="primary"):
        stored_cv = st.session_state.get("extracted_cv_text", st.session_state.cv_text_draft) if save_cv else profile["cv_text"]
        storage.save_profile(uid, claims, target, profile["location"], profile["education"],
                             profile["about"], stored_cv)
        st.success("Skills, learning goal and CV text saved to your private profile.")
    st.subheader("Claimed vs assessed")
    rows = []
    for skill in claims:
        rows.append({"Skill": skill, "Claim": "Claimed by learner", "Evidence":
                     f"{len(history)} Python attempts recorded; see topic results" if skill == "Python" and history else "Not assessed"})
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("Add at least one skill claim to see its assessment status.")
    st.dataframe(pd.DataFrame(summarize(history)), hide_index=True, width="stretch")
