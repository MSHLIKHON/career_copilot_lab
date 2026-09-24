import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

# Add generic job-related words to stop words to filter out non-technical terms
CUSTOM_STOP_WORDS = list(ENGLISH_STOP_WORDS) + [
    'experience', 'ability', 'proven', 'strong', 'level', 'track', 'record', 
    'candidate', 'skills', 'required', 'requirements', 'knowledge', 'understanding',
    'working', 'excellent', 'years', 'hands', 'demonstrate', 'mandatory', 'end',
    'advanced', 'proficiency', 'support', 'management', 'building', 'using', 'work',
    'team', 'development', 'design', 'business', 'data', 'software', 'systems', 
    'application', 'ensure', 'role', 'including', 'position', 'documents'
]

def analyze_job_match(cv_text, job_text, user_claims):
    # If no CV text is provided, use their claimed skills as their document
    if not cv_text.strip():
        cv_text = " ".join(user_claims)
        
    if not job_text.strip() or not cv_text.strip():
        return 0.0, []

    # 1. Feature Extraction using TF-IDF with 1- and 2-word phrases (Unigrams & Bigrams)
    vectorizer = TfidfVectorizer(stop_words=CUSTOM_STOP_WORDS, ngram_range=(1, 2))

    try:
        # Create vectors for both documents
        tfidf_matrix = vectorizer.fit_transform([cv_text.lower(), job_text.lower()])
        
        # Calculate Cosine Similarity between the two vectors
        match_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # 2. Dynamic Skill Gap Extraction (Unsupervised ML)
        feature_names = np.array(vectorizer.get_feature_names_out())
        cv_vec = tfidf_matrix[0].toarray()[0]
        job_vec = tfidf_matrix[1].toarray()[0]
        
        gaps = []
        for i, name in enumerate(feature_names):
            # If the term has weight in the job description but ZERO weight in the CV
            if job_vec[i] > 0 and cv_vec[i] == 0:
                # Filter out pure numbers or very short words
                if not name.isnumeric() and len(name) > 2:
                    gaps.append((name.title(), job_vec[i]))
                    
        # Sort gaps by their TF-IDF importance in the job description
        gaps.sort(key=lambda x: x[1], reverse=True)
        
        # Take the top 15 most important missing keywords
        missing_skills = [gap[0] for gap in gaps[:15]]
        
    except ValueError:
        match_score = 0.0
        missing_skills = []
    
    return round(match_score * 100, 1), missing_skills

