import re
import joblib
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
try:
    KNOWN_SKILLS = joblib.load(MODEL_DIR / "skill_vocab.joblib")
    # Sort by length descending so longer phrases match before their sub-words
    KNOWN_SKILLS = sorted(KNOWN_SKILLS, key=len, reverse=True)
except Exception:
    # Fallback if model not trained yet
    KNOWN_SKILLS = []

# Filter out generic words that Kaggle considers skills but are too broad
GENERIC_SKILL_FILTER = {
    'computer science', 'troubleshooting', 'configuration', 'applications', 'engineering',
    'testing', 'automation', 'scripting', 'problem-solving', 'problem-solving skills',
    'root cause analysis', 'quality assurance', 'communication', 'communication skills',
    'operations', 'management', 'support', 'documentation', 'planning', 'design',
    'analysis', 'research', 'leadership', 'teamwork', 'coordination', 'strategy',
    'development', 'maintenance', 'integration', 'architecture', 'software', 'hardware',
    'infrastructure management', 'system administration', 'systems', 'information technology',
    'project management', 'business', 'process', 'customer service', 'sales', 'marketing'
}

def analyze_job_match(cv_text, job_text, user_claims):
    """
    Analyzes the match between a CV and a Job Description.
    Calculates TF-IDF Cosine Similarity for the score.
    Uses the trained Kaggle Dataset vocabulary to accurately extract Missing Skills.
    """
    if not cv_text.strip():
        cv_text = " ".join(user_claims)
        
    if not job_text.strip() or not cv_text.strip():
        return 0.0, []

    # 1. Similarity Score using TF-IDF
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([cv_text.lower(), job_text.lower()])
        match_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except ValueError:
        match_score = 0.0

    # 2. Dynamic Skill Gap Extraction using the Trained Kaggle Dataset
    job_text_lower = job_text.lower()
    cv_text_lower = cv_text.lower()
    
    job_skills = []
    
    # Iterate over the 4,900+ known skills from the Kaggle Dataset
    for skill in KNOWN_SKILLS:
        if len(skill) < 2: 
            pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        else:
            pattern = r"\b" + re.escape(skill) + r"\b"
            
        if re.search(pattern, job_text_lower):
            job_skills.append(skill.title())
            # Replace found skill with spaces to prevent overlapping sub-skill extraction
            # e.g., prevents finding "Active" after finding "Active Directory"
            job_text_lower = re.sub(pattern, " "*len(skill), job_text_lower)
            
    # Check which job_skills are NOT in the user's CV
    missing_skills = []
    user_claims_lower = [c.lower() for c in user_claims]
    
    for skill in job_skills:
        skill_lower = skill.lower()
        
        # Skip generic skills
        if skill_lower in GENERIC_SKILL_FILTER:
            continue
            
        if skill_lower not in user_claims_lower:
            # Also verify it's not anywhere in the full CV text
            if not re.search(r"\b" + re.escape(skill_lower) + r"\b", cv_text_lower):
                missing_skills.append(skill)
                
    return round(match_score * 100, 1), missing_skills[:15]

def generate_roadmap(missing_skills):
    """Dynamically generates actionable learning resources for any missing skill without hardcoding."""
    recommendations = []
    for skill in missing_skills:
        encoded_skill = skill.replace(" ", "%20")
        
        resource = {
            "title": f"Mastering {skill}",
            "type": "Dynamic Learning Path",
            "description": f"Bridge your skill gap in **{skill}**. Choose your preferred platform below to find the most up-to-date, top-rated courses:",
            "links": {
                "Coursera": f"https://www.coursera.org/search?query={encoded_skill}",
                "Udemy": f"https://www.udemy.com/courses/search/?q={encoded_skill}",
                "YouTube": f"https://www.youtube.com/results?search_query={encoded_skill}+full+course"
            }
        }
        recommendations.append((skill, resource))
    return recommendations
