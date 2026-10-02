import json
import streamlit as st
from core import storage
from core.job_ml import analyze_job_match, generate_roadmap

def render_job_analyzer(uid, profile):
    st.caption("CAREER PREPARATION")
    st.title("Job Match Analyzer")
    st.write("Compare CV/profile text with a job description using local TF-IDF text similarity and a trained skill vocabulary.")
    st.caption("This is a learning aid, not a hiring score. Similar wording can raise the score, and extracted skills can be incomplete.")
    analyze_tab, saved_tab = st.tabs(["New analysis", "Saved roadmaps"])
    with analyze_tab:
        job_text = st.text_area("Job description", height=220, max_chars=50000)
        cv_text = st.text_area("CV text", value=profile["cv_text"], height=140, max_chars=50000,
                               help="Your saved profile CV is loaded automatically. If empty, saved skill claims are used.")
        if st.button("Analyze job match", type="primary"):
            if not job_text.strip():
                st.error("Paste a job description first.")
            else:
                scores, missing_skills = analyze_job_match(cv_text, job_text, profile["claims"])
                st.session_state.job_analysis = {
                    "score": scores["combined_score"], "scores": scores, "missing_skills": missing_skills,
                    "roadmaps": generate_roadmap(missing_skills), "job_text": job_text,
                }
        analysis = st.session_state.get("job_analysis")
        if analysis:
            st.subheader("Analysis result")
            if "scores" in analysis:
                scores = analysis["scores"]
                a, b, c = st.columns(3)
                a.metric("Match Score", f"{scores['combined_score']}%", help="Combined score giving more weight to direct skill matches")
                b.metric("ATS Skill Match", f"{scores['ats_score']}%", help="Percentage of required skills found in your profile")
                c.metric("Text Similarity", f"{scores['ml_score']}%", help="TF-IDF semantic similarity")
                st.metric("Missing technical skills", len(analysis["missing_skills"]))
            else:
                a, b = st.columns(2)
                a.metric("Text similarity", f"{analysis['score']}%")
                b.metric("Missing technical skills", len(analysis["missing_skills"]))
            if analysis["missing_skills"]:
                st.write("**Detected gaps:** " + ", ".join(analysis["missing_skills"]))
                st.subheader("Learning searches")
                for skill, resource in analysis["roadmaps"]:
                    with st.expander(skill):
                        st.write(resource["description"])
                        cols = st.columns(len(resource["links"]))
                        for col, (platform, url) in zip(cols, resource["links"].items()):
                            col.link_button(platform, url, width="stretch")
            else:
                st.success("No missing skill from the available vocabulary was detected.")
            with st.form("save_job_analysis"):
                title = st.text_input("Job title for this saved roadmap", max_chars=120)
                save_analysis = st.form_submit_button("Save analysis")
            if save_analysis:
                try:
                    storage.save_job_analysis(uid, title, analysis["job_text"], analysis["score"],
                                              analysis["missing_skills"], analysis["roadmaps"])
                    st.success("Analysis saved.")
                except ValueError as error:
                    st.error(str(error))
    with saved_tab:
        saved_jobs = storage.get_saved_jobs(uid)
        if not saved_jobs:
            st.info("No saved job analyses yet.")
        for saved in saved_jobs:
            with st.expander(f"{saved['title']} · {saved['score']:.1f}%"):
                try:
                    missing = json.loads(saved["missing_skills"])
                    roadmaps = json.loads(saved["roadmaps"])
                except (TypeError, json.JSONDecodeError):
                    st.error("This saved analysis is damaged and cannot be displayed.")
                    continue
                st.write("**Missing skills:** " + (", ".join(missing) if missing else "None detected"))
                for skill, resource in roadmaps:
                    st.write(f"**{skill}** — {resource['description']}")
                if st.button("Delete saved analysis", key=f"delete_job_{saved['id']}"):
                    storage.delete_saved_job(uid, saved["id"])
                    st.rerun()
