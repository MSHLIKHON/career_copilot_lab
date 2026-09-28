import re
import joblib
from pathlib import Path
from urllib.parse import quote_plus

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
try:
    KNOWN_SKILLS = joblib.load(MODEL_DIR / "skill_vocab.joblib")
    if not isinstance(KNOWN_SKILLS, (list, tuple, set)):
        raise ValueError("Skill vocabulary must be a collection.")
    KNOWN_SKILLS = sorted({skill.strip().lower() for skill in KNOWN_SKILLS
                           if isinstance(skill, str) and 1 <= len(skill.strip()) <= 100},
                          key=len, reverse=True)
except Exception:
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

def _skill_pattern(skill):
    return r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"


def analyze_job_match(cv_text, job_text, user_claims):
    """Return a text-similarity score and job skills absent from the CV/profile."""
    if not isinstance(cv_text, str) or not isinstance(job_text, str):
        raise ValueError("CV and job description must be text.")
    if not isinstance(user_claims, list) or any(not isinstance(claim, str) for claim in user_claims):
        raise ValueError("Saved skill claims are invalid.")
    cv_text = cv_text[:50000]
    job_text = job_text[:50000]
    if not cv_text.strip():
        cv_text = " ".join(user_claims)

    if not job_text.strip() or not cv_text.strip():
        return 0.0, []

    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
        tfidf_matrix = vectorizer.fit_transform([cv_text.lower(), job_text.lower()])
        match_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except ValueError:
        match_score = 0.0

    job_text_lower = job_text.lower()
    cv_text_lower = cv_text.lower()
    job_skills = []

    for skill in KNOWN_SKILLS:
        pattern = _skill_pattern(skill)
        if re.search(pattern, job_text_lower):
            job_skills.append(skill.title())
            job_text_lower = re.sub(pattern, " " * len(skill), job_text_lower)

    missing_skills = []
    user_claims_lower = {claim.lower() for claim in user_claims}

    for skill in job_skills:
        skill_lower = skill.lower()
        if skill_lower in GENERIC_SKILL_FILTER:
            continue
        if skill_lower not in user_claims_lower and not re.search(_skill_pattern(skill_lower), cv_text_lower):
            missing_skills.append(skill)

    return round(match_score * 100, 1), missing_skills[:15]


def generate_roadmap(missing_skills):
    """Generate search links rather than claiming that unreviewed courses are curated."""
    recommendations = []
    for skill in missing_skills[:15]:
        encoded_skill = quote_plus(skill)
        resource = {
            "title": f"Mastering {skill}",
            "type": "Course search links",
            "description": f"Explore current learning material for {skill}. Review provider, level, price and quality yourself.",
            "links": {
                "Coursera": f"https://www.coursera.org/search?query={encoded_skill}",
                "Udemy": f"https://www.udemy.com/courses/search/?q={encoded_skill}",
                "YouTube": f"https://www.youtube.com/results?search_query={encoded_skill}+full+course",
            },
        }
        recommendations.append((skill, resource))
    return recommendations
