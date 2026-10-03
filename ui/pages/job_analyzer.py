import json
import html
from datetime import datetime
import streamlit as st
from core import storage
from core.job_ml import analyze_job_match, generate_roadmap

JOB_ANALYZER_CSS = """
<style>
.skill-list-container {
    display: flex;
    flex-direction: column;
    gap: 9px;
    margin-top: 10px;
    margin-bottom: 22px;
}
.skill-row {
    background: #ffffff;
    border: 1px solid #DEE6F1;
    border-radius: 12px;
    padding: 11px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    box-shadow: 0 2px 10px rgba(23, 52, 91, 0.03);
    transition: all 0.16s ease-in-out;
}
.skill-row:hover {
    border-color: #B9CEF3;
    box-shadow: 0 4px 16px rgba(23, 52, 91, 0.07);
    transform: translateY(-1px);
}
.skill-info {
    display: inline-flex;
    align-items: center;
    gap: 9px;
}
.skill-bullet {
    color: #244A83;
    font-size: 13px;
}
.skill-name {
    font-size: 14.5px;
    font-weight: 700;
    color: #17243D;
    letter-spacing: -0.01em;
}
.gap-tag {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 999px;
    background: #FFF1F0;
    border: 1px solid #FFCCC7;
    color: #CF1322;
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 0.02em;
}
.skill-links {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.resource-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none !important;
    border: 1px solid #DCE6F3;
    background: #F8FAFD;
    color: #244A83 !important;
    transition: all 0.15s ease;
}
.resource-link:hover {
    transform: translateY(-1px);
}
.resource-link.coursera {
    background: #F0F5FF;
    border-color: #D0E1FD;
    color: #0056D2 !important;
}
.resource-link.coursera:hover {
    background: #E1EDFE;
    border-color: #ADC8FB;
}
.resource-link.udemy {
    background: #FAF3FF;
    border-color: #EBD6FC;
    color: #7928CA !important;
}
.resource-link.udemy:hover {
    background: #F3E5FD;
    border-color: #DCBAFA;
}
.resource-link.youtube {
    background: #FEF2F2;
    border-color: #FCD5D5;
    color: #DC2626 !important;
}
.resource-link.youtube:hover {
    background: #FEE2E2;
    border-color: #FCA5A5;
}
.brand-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px;
    height: 15px;
    font-size: 9.5px;
    font-weight: 800;
    line-height: 1;
    margin-right: 4px;
    vertical-align: -1px;
    user-select: none;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.brand-badge.coursera {
    background: #0056D2;
    color: #ffffff !important;
    border-radius: 50%;
}
.brand-badge.udemy {
    background: #A435F0;
    color: #ffffff !important;
    border-radius: 4px;
}
.brand-badge.youtube {
    background: #DC2626;
    color: #ffffff !important;
    border-radius: 4px;
    font-size: 8px;
    padding-left: 1px;
}
</style>
"""


def _render_skill_rows(roadmaps):
    """Render sleek, compact skill gap rows with direct learning search links."""
    html_items = []
    for skill, resource in roadmaps:
        links = resource.get("links", {})
        safe_skill = html.escape(str(skill))
        coursera = html.escape(str(links.get("Coursera", f"https://www.coursera.org/search?query={skill}")), quote=True)
        udemy = html.escape(str(links.get("Udemy", f"https://www.udemy.com/courses/search/?q={skill}")), quote=True)
        youtube = html.escape(str(links.get("YouTube", f"https://www.youtube.com/results?search_query={skill}+full+course")), quote=True)

        item_html = (
            '<div class="skill-row">'
            '<div class="skill-info">'
            '<span class="skill-bullet">&#9670;</span>'
            f'<span class="skill-name">{safe_skill}</span>'
            '<span class="gap-tag">Skill Gap</span>'
            '</div>'
            '<div class="skill-links">'
            f'<a href="{coursera}" target="_blank" rel="noopener noreferrer" class="resource-link coursera">'
            '<span class="brand-badge coursera">C</span>Coursera'
            '</a>'
            f'<a href="{udemy}" target="_blank" rel="noopener noreferrer" class="resource-link udemy">'
            '<span class="brand-badge udemy">U</span>Udemy'
            '</a>'
            f'<a href="{youtube}" target="_blank" rel="noopener noreferrer" class="resource-link youtube">'
            '<span class="brand-badge youtube">&#9654;</span>YouTube'
            '</a>'
            '</div>'
            '</div>'
        )
        html_items.append(item_html)

    full_html = f'<div class="skill-list-container">{"".join(html_items)}</div>'
    if hasattr(st, "html"):
        st.html(full_html)
    else:
        st.markdown(full_html, unsafe_allow_html=True)


def render_job_analyzer(uid, profile):
    if hasattr(st, "html"):
        st.html(JOB_ANALYZER_CSS)
    else:
        st.markdown(JOB_ANALYZER_CSS, unsafe_allow_html=True)
    st.caption("CAREER PREPARATION")
    st.title("Job Match Analyzer")
    st.write("Compare CV/profile text with a job description using local TF-IDF text similarity and a trained skill vocabulary.")
    st.caption("This is a learning aid, not a hiring score. Similar wording can raise the score, and extracted skills can be incomplete.")

    analyze_tab, saved_tab = st.tabs(["New analysis", "Saved roadmaps"])

    with analyze_tab:
        job_text = st.text_area("Job description", height=200, max_chars=50000, placeholder="Paste job description or requirements here...")
        cv_text = st.text_area("CV text", value=profile["cv_text"], height=130, max_chars=50000,
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
            scores = analysis.get("scores")
            if scores:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Overall Match", f"{scores['combined_score']}%", help="Weighted blend: 60% ATS skill match + 40% semantic similarity")
                c2.metric("ATS Skill Match", f"{scores['ats_score']}%", help="Direct required technical skills matched in your CV")
                c3.metric("Semantic Similarity", f"{scores['ml_score']}%", help="TF-IDF contextual text similarity")
                c4.metric("Skill Gaps", f"{len(analysis['missing_skills'])} detected", help="Required technical skills absent from CV")
            else:
                c1, c2 = st.columns(2)
                c1.metric("Text similarity", f"{analysis['score']}%")
                c2.metric("Missing technical skills", len(analysis["missing_skills"]))

            if analysis["missing_skills"]:
                st.markdown("### Detected Skill Gaps & Recommended Learning")
                st.caption("Required technical skills missing from your CV. Click any platform for targeted courses and search results.")
                _render_skill_rows(analysis["roadmaps"])
            else:
                st.success("No missing technical skills from the known vocabulary were detected. Excellent alignment!")

            with st.expander("🔖 Bookmark roadmap to profile", expanded=False):
                with st.form("save_job_analysis"):
                    title = st.text_input("Role / Job title", placeholder="e.g. Senior Backend Engineer", max_chars=120)
                    save_analysis = st.form_submit_button("Bookmark Roadmap", type="primary")
                if save_analysis:
                    try:
                        storage.save_job_analysis(uid, title, analysis["job_text"], analysis["score"],
                                                  analysis["missing_skills"], analysis["roadmaps"])
                        st.success("Analysis saved successfully.")
                    except ValueError as error:
                        st.error(str(error))

    with saved_tab:
        saved_jobs = storage.get_saved_jobs(uid)
        if not saved_jobs:
            st.info("No saved job analyses yet. Analyze a job description to save its roadmap here.")
        for saved in saved_jobs:
            created_ts = saved.get("created")
            saved_date = datetime.fromtimestamp(created_ts).strftime("%d %b %Y") if created_ts else "Saved"
            expander_title = f"{saved['title']} — {saved['score']:.1f}% Match ({saved_date})"

            with st.expander(expander_title):
                try:
                    missing = json.loads(saved["missing_skills"])
                    roadmaps = json.loads(saved["roadmaps"])
                except (TypeError, json.JSONDecodeError):
                    st.error("This saved analysis is damaged and cannot be displayed.")
                    continue

                col_meta, col_del = st.columns([3, 1])
                with col_meta:
                    st.markdown(f"**Overall Match:** `{saved['score']:.1f}%` &nbsp;&bull;&nbsp; **Skill Gaps:** `{len(missing)}`")
                with col_del:
                    if st.button("Delete Roadmap", key=f"delete_job_{saved['id']}", type="secondary", use_container_width=True):
                        storage.delete_saved_job(uid, saved["id"])
                        st.rerun()

                if roadmaps:
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                    _render_skill_rows(roadmaps)
                else:
                    st.info("No skill gaps were detected for this saved role.")
