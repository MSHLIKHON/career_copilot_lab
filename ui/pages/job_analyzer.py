"""Job Circular Analyzer page."""

import streamlit as st
from core.job_ml import analyze_job_match

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
            st.write("The job description mentions these skills which are **missing** from your profile:")
            for skill in missing_skills:
                st.markdown(f"- 🔴 **{skill}**")
            
            st.write("\n**Recommendation:** Practice these topics in the coding workspace or seek out projects that use these technologies.")
        else:
            st.success("Great job! No major missing skills detected from our known list.")
            
        with st.expander("Your Current Claimed Skills"):
            st.write(", ".join(profile["claims"]) if profile["claims"] else "None")
