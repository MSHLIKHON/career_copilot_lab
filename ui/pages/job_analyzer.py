"""Job Circular Analyzer page."""

import streamlit as st
from core.job_ml import analyze_job_match, generate_roadmap

def render_job_analyzer(user: dict, history: list, profile: dict) -> None:
    st.caption("CAREER PREPARATION")
    st.title("Job Match Analyzer")
    st.write("Paste a job description and see how well your profile matches the requirements.")
        
    job_text = st.text_area("Job Description Text", height=200, help="Paste the text of the job circular here.")
    
    with st.expander("Provide full CV text (Optional)"):
        cv_text = st.text_area("Full CV Text", height=150, help="Paste your full CV text for a more accurate ML match score. If left blank, we will use your saved skills.")
        
    if st.button("Analyze Match", type="primary"):
        if not job_text:
            st.error("Please paste a job description to analyze.")
            return
            
        with st.spinner("Running ML analysis..."):
            score, missing_skills = analyze_job_match(cv_text, job_text, profile["claims"])
            
        st.subheader("Analysis Results")
        
        # Display Score
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("ML Match Score", f"{score}%")
            
        with col2:
            if score > 75:
                st.success("High match! You are a strong candidate for this role.")
            elif score > 40:
                st.warning("Moderate match. You have some foundational skills, but there are gaps.")
            else:
                st.error("Low match. Significant upskilling is recommended before applying.")
                
        st.divider()
        
        # Display Gaps
        st.subheader("Skill Gap Analysis")
        if missing_skills:
            st.write("The job description mentions these technical skills which are missing from your profile:")
            
            # Display skills as modern badges/pills
            badges = ""
            for skill in missing_skills:
                badges += f'<span style="background-color: #1e3a8a; color: white; padding: 6px 16px; border-radius: 20px; margin: 4px; display: inline-block; font-size: 14px; font-weight: 600;">{skill}</span>'
            st.markdown(f"<div style='margin-top: 10px; margin-bottom: 20px;'>{badges}</div>", unsafe_allow_html=True)
            
            st.divider()
            st.subheader("Recommended Learning Roadmap")
            st.write("Based on your specific skill gaps, we recommend the following curated learning paths to prepare for this job:")
            
            roadmaps = generate_roadmap(missing_skills)
            
            if roadmaps:
                for skill, r in roadmaps:
                    with st.container(border=True):
                        st.markdown(f"**{skill} Learning Path**")
                        st.write(r['description'])
                        
                        # Display links clearly
                        links_html = " &nbsp;|&nbsp; ".join([f"<a href='{url}' target='_blank' style='text-decoration: none; font-weight: bold;'>{platform}</a>" for platform, url in r['links'].items()])
                        st.markdown(links_html, unsafe_allow_html=True)
            
        else:
            st.success("Great job! No major missing technical skills detected.")
            
        with st.expander("Your Current Claimed Skills"):
            st.write(", ".join(profile["claims"]) if profile["claims"] else "None")
