import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from core.adaptive import SKILLS

EXTENDED_SKILLS = list(set(SKILLS + [
    "Django", "Flask", "Docker", "Git", "AWS", "Azure", "C++", 
    "C#", "Ruby", "PHP", "Node.js", "TypeScript", "Linux", 
    "Kubernetes", "Machine Learning", "Data Analysis", "API",
    "REST", "GraphQL", "Agile", "Scrum", "CI/CD"
]))

def analyze_job_match(cv_text, job_text, user_claims):
    """
    Analyzes the match between a CV and a Job Description using TF-IDF and Cosine Similarity.
    """
    # 1. Feature Extraction using TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # If no CV text is provided, use their claimed skills as their document
    if not cv_text.strip():
        cv_text = " ".join(user_claims)
        
    if not job_text.strip() or not cv_text.strip():
        return 0.0, []

    try:
        # Create vectors for both documents
        tfidf_matrix = vectorizer.fit_transform([cv_text.lower(), job_text.lower()])
        # Calculate Cosine Similarity between the two vectors
        match_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except ValueError:
        match_score = 0.0

    # 2. Skill Gap Extraction
    job_text_lower = job_text.lower()
    job_skills = []
    
    for skill in EXTENDED_SKILLS:
        # Match standalone skills (ignoring partial word matches inside larger words)
        if re.search(r"(?<![a-z])" + re.escape(skill.lower()) + r"(?![a-z])", job_text_lower):
            job_skills.append(skill)
            
    # Find which skills are in the job description but missing from the user's profile
    missing_skills = [s for s in job_skills if s not in user_claims]
    
    return round(match_score * 100, 1), missing_skills
