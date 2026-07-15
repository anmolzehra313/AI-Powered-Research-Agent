"""
Plagiarism Detection Utilities Module

Provides functions for detecting text similarity using:
- TF-IDF + Cosine Similarity
- Sentence Transformers (all-MiniLM-L6-v2)
- Sentence-level comparison with highlighting
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

from nltk.tokenize import sent_tokenize


def split_into_sentences(text):
    """Split text into sentences using NLTK."""
    try:
        return sent_tokenize(text)
    except Exception:
        # Fallback: split on period + space
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]


def tfidf_similarity(text1, text2):
    """
    Calculate overall similarity between two texts using TF-IDF + Cosine Similarity.
    
    Args:
        text1: First text document.
        text2: Second text document.
        
    Returns:
        Similarity score between 0 and 1.
    """
    try:
        vectorizer = TfidfVectorizer(stop_words='english', min_df=1)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        print(f"TF-IDF similarity calculation failed: {e}")
        return 0.0


def sentence_transformer_similarity(text1, text2, model=None):
    """
    Calculate similarity using Sentence Transformers embeddings.
    
    Args:
        text1: First text document.
        text2: Second text document.
        model: Pre-loaded SentenceTransformer model (optional).
        
    Returns:
        Similarity score between 0 and 1.
    """
    try:
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')

        embeddings = model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(max(0, similarity))
    except Exception as e:
        print(f"Sentence transformer similarity failed: {e}")
        return 0.0


def find_matching_sentences(text1, text2, threshold=0.7, model=None):
    """
    Find matching sentences between two texts using sentence embeddings.
    
    Args:
        text1: Source text.
        text2: Comparison text.
        threshold: Minimum similarity score to consider a match (0-1).
        model: Pre-loaded SentenceTransformer model (optional).
        
    Returns:
        List of dictionaries with matching sentence pairs and scores.
    """
    try:
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')

        sentences1 = split_into_sentences(text1)
        sentences2 = split_into_sentences(text2)

        if not sentences1 or not sentences2:
            return []

        # Encode all sentences
        embeddings1 = model.encode(sentences1)
        embeddings2 = model.encode(sentences2)

        # Calculate pairwise similarity
        sim_matrix = cosine_similarity(embeddings1, embeddings2)

        matches = []
        for i in range(len(sentences1)):
            for j in range(len(sentences2)):
                score = float(sim_matrix[i][j])
                if score >= threshold:
                    matches.append({
                        'source_sentence': sentences1[i],
                        'matching_sentence': sentences2[j],
                        'similarity_score': round(score, 4),
                        'source_index': i,
                        'match_index': j,
                    })

        # Sort by similarity score (highest first)
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Remove duplicate matches (keep highest score per source sentence)
        seen_sources = set()
        unique_matches = []
        for match in matches:
            if match['source_index'] not in seen_sources:
                seen_sources.add(match['source_index'])
                unique_matches.append(match)

        return unique_matches

    except Exception as e:
        print(f"Sentence matching failed: {e}")
        return []


def calculate_plagiarism_percentage(text1, text2, model=None):
    """
    Calculate overall plagiarism percentage combining multiple methods.
    
    Args:
        text1: Source text.
        text2: Comparison text.
        model: Pre-loaded SentenceTransformer model (optional).
        
    Returns:
        Dictionary with scores from different methods and overall percentage.
    """
    # TF-IDF similarity
    tfidf_score = tfidf_similarity(text1, text2)

    # Sentence transformer similarity
    st_score = sentence_transformer_similarity(text1, text2, model)

    # Sentence-level matching
    matches = find_matching_sentences(text1, text2, threshold=0.7, model=model)
    sentences1 = split_into_sentences(text1)
    matched_ratio = len(matches) / max(len(sentences1), 1)

    # Combined score (weighted average)
    overall_score = (0.3 * tfidf_score) + (0.4 * st_score) + (0.3 * matched_ratio)

    return {
        'tfidf_similarity': round(tfidf_score * 100, 2),
        'semantic_similarity': round(st_score * 100, 2),
        'sentence_match_ratio': round(matched_ratio * 100, 2),
        'overall_plagiarism_score': round(overall_score * 100, 2),
        'matching_sentences': matches,
        'total_source_sentences': len(sentences1),
        'matched_sentence_count': len(matches),
    }


def generate_plagiarism_report(result):
    """
    Generate a formatted text report from plagiarism detection results.
    
    Args:
        result: Dictionary from calculate_plagiarism_percentage().
        
    Returns:
        Formatted report string.
    """
    report = []
    report.append("=" * 60)
    report.append("PLAGIARISM DETECTION REPORT")
    report.append("=" * 60)
    report.append("")
    report.append(f"Overall Plagiarism Score: {result['overall_plagiarism_score']}%")
    report.append("")
    report.append("--- Detailed Scores ---")
    report.append(f"TF-IDF Cosine Similarity: {result['tfidf_similarity']}%")
    report.append(f"Semantic Similarity: {result['semantic_similarity']}%")
    report.append(f"Sentence Match Ratio: {result['sentence_match_ratio']}%")
    report.append("")
    report.append(f"Total Source Sentences: {result['total_source_sentences']}")
    report.append(f"Matched Sentences: {result['matched_sentence_count']}")
    report.append("")

    if result['matching_sentences']:
        report.append("--- Matching Sentences ---")
        report.append("")
        for i, match in enumerate(result['matching_sentences'], 1):
            report.append(f"Match {i} (Similarity: {match['similarity_score'] * 100:.1f}%):")
            report.append(f"  Source:  {match['source_sentence']}")
            report.append(f"  Target:  {match['matching_sentence']}")
            report.append("")

    report.append("=" * 60)
    report.append("END OF REPORT")
    report.append("=" * 60)

    return '\n'.join(report)


def highlight_matching_text(text, matches, role='source'):
    """
    Create HTML with highlighted matching sentences.
    
    Args:
        text: Original text.
        matches: List of match dictionaries from find_matching_sentences().
        role: 'source' or 'target' to determine which sentences to highlight.
        
    Returns:
        HTML string with highlighted matching portions.
    """
    if not matches:
        return text

    key = 'source_sentence' if role == 'source' else 'matching_sentence'
    matching_texts = {m[key] for m in matches}

    sentences = split_into_sentences(text)
    highlighted_parts = []

    for sentence in sentences:
        if sentence in matching_texts:
            # Find the similarity score for this sentence
            score = 0
            for m in matches:
                if m[key] == sentence:
                    score = m['similarity_score']
                    break
            # Color intensity based on similarity score
            intensity = int(255 * (1 - score * 0.5))
            color = f"rgb(255, {intensity}, {intensity})"
            highlighted_parts.append(
                f'<span style="background-color: {color}; padding: 2px 4px; '
                f'border-radius: 3px;" title="Similarity: {score*100:.1f}%">{sentence}</span>'
            )
        else:
            highlighted_parts.append(sentence)

    return ' '.join(highlighted_parts)
