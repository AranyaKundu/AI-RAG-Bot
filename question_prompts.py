from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def analyze_user_input(user_prompt, question_database):
    vectorizer = TfidfVectorizer()
    all_texts = list(question_database.keys()) + [user_prompt]
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    most_relevant_topics = list(question_database.keys())[similarity_scores.argmax()]
    
