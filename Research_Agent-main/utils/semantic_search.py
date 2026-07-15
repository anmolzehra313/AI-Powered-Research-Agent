"""
Semantic Search Utilities Module

Provides functions for:
- Paper search across Semantic Scholar, arXiv, and CrossRef APIs
- Semantic similarity using Sentence Transformers and FAISS
- TF-IDF based similarity search
"""

import re
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==================== API Search Functions ====================

def search_semantic_scholar(query, limit=10):
    """
    Search papers on Semantic Scholar API.
    
    Args:
        query: Search query string.
        limit: Maximum number of results to return.
        
    Returns:
        List of paper dictionaries with standardized fields.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        'query': query,
        'limit': limit,
        'fields': 'title,authors,abstract,year,citationCount,externalIds,url,openAccessPdf',
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for paper in data.get('data', []):
            external_ids = paper.get('externalIds', {}) or {}
            pdf_info = paper.get('openAccessPdf', {}) or {}
            authors_list = paper.get('authors', []) or []

            papers.append({
                'title': paper.get('title', 'N/A'),
                'authors': ', '.join([a.get('name', '') for a in authors_list]),
                'abstract': paper.get('abstract', 'No abstract available'),
                'year': paper.get('year', 'N/A'),
                'citation_count': paper.get('citationCount', 0),
                'doi': external_ids.get('DOI', ''),
                'pdf_url': pdf_info.get('url', ''),
                'source': 'Semantic Scholar',
                'url': paper.get('url', ''),
            })

        return papers

    except requests.exceptions.RequestException as e:
        print(f"Semantic Scholar API error: {e}")
        return []


def search_arxiv(query, limit=10):
    """
    Search papers on arXiv API.
    
    Args:
        query: Search query string.
        limit: Maximum number of results.
        
    Returns:
        List of paper dictionaries.
    """
    try:
        import arxiv

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        papers = []
        for result in client.results(search):
            papers.append({
                'title': result.title,
                'authors': ', '.join([a.name for a in result.authors]),
                'abstract': result.summary,
                'year': result.published.year if result.published else 'N/A',
                'citation_count': 'N/A',
                'doi': result.doi or '',
                'pdf_url': result.pdf_url or '',
                'source': 'arXiv',
                'url': result.entry_id,
            })

        return papers

    except Exception as e:
        print(f"arXiv API error: {e}")
        return []


def search_crossref(query, limit=10):
    """
    Search papers on CrossRef API.
    
    Args:
        query: Search query string.
        limit: Maximum number of results.
        
    Returns:
        List of paper dictionaries.
    """
    url = "https://api.crossref.org/works"
    params = {
        'query': query,
        'rows': limit,
        'select': 'DOI,title,author,abstract,published-print,is-referenced-by-count,URL,link',
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        papers = []
        for item in data.get('message', {}).get('items', []):
            title_list = item.get('title', ['N/A'])
            title = title_list[0] if title_list else 'N/A'

            authors = item.get('author', [])
            author_str = ', '.join(
                [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors]
            )

            # Get year
            date_parts = item.get('published-print', {}).get('date-parts', [[]])
            year = date_parts[0][0] if date_parts and date_parts[0] else 'N/A'

            # Get PDF link
            pdf_url = ''
            for link in item.get('link', []):
                if 'pdf' in link.get('content-type', '').lower():
                    pdf_url = link.get('URL', '')
                    break

            # Clean abstract (remove XML tags)
            abstract = item.get('abstract', 'No abstract available')
            abstract = re.sub(r'<[^>]+>', '', abstract) if abstract else 'No abstract available'

            papers.append({
                'title': title,
                'authors': author_str,
                'abstract': abstract,
                'year': year,
                'citation_count': item.get('is-referenced-by-count', 0),
                'doi': item.get('DOI', ''),
                'pdf_url': pdf_url,
                'source': 'CrossRef',
                'url': item.get('URL', ''),
            })

        return papers

    except requests.exceptions.RequestException as e:
        print(f"CrossRef API error: {e}")
        return []


def search_all_sources(query, limit_per_source=5):
    """
    Search across all available APIs and merge results.
    
    Args:
        query: Search query string.
        limit_per_source: Maximum results per source.
        
    Returns:
        Combined list of paper dictionaries.
    """
    all_papers = []

    # Search each source
    results_ss = search_semantic_scholar(query, limit_per_source)
    all_papers.extend(results_ss)

    results_arxiv = search_arxiv(query, limit_per_source)
    all_papers.extend(results_arxiv)

    results_cr = search_crossref(query, limit_per_source)
    all_papers.extend(results_cr)

    return all_papers


# ==================== Similarity Search Functions ====================

def compute_tfidf_similarity(query_text, documents):
    """
    Compute TF-IDF cosine similarity between a query and a list of documents.
    
    Args:
        query_text: Query string.
        documents: List of document strings.
        
    Returns:
        List of (index, score) tuples sorted by score descending.
    """
    if not documents:
        return []

    try:
        all_texts = [query_text] + documents
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Compute similarity between query and all documents
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        # Return sorted results
        results = [(i, float(score)) for i, score in enumerate(similarities)]
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    except Exception as e:
        print(f"TF-IDF similarity computation failed: {e}")
        return []


def compute_semantic_similarity(query_text, documents, model=None):
    """
    Compute semantic similarity using Sentence Transformers and FAISS.
    
    Args:
        query_text: Query string.
        documents: List of document strings.
        model: Pre-loaded SentenceTransformer model (optional).
        
    Returns:
        List of (index, score) tuples sorted by score descending.
    """
    if not documents:
        return []

    try:
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')

        # Encode query and documents
        query_embedding = model.encode([query_text])
        doc_embeddings = model.encode(documents)

        # Try FAISS for efficient search
        try:
            import faiss
            dimension = doc_embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine after normalization)

            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(doc_embeddings)
            faiss.normalize_L2(query_embedding)

            index.add(doc_embeddings.astype(np.float32))
            scores, indices = index.search(query_embedding.astype(np.float32), min(len(documents), 50))

            results = [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0]) if idx >= 0]
            return results

        except ImportError:
            # Fallback to sklearn cosine similarity
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
            results = [(i, float(score)) for i, score in enumerate(similarities)]
            results.sort(key=lambda x: x[1], reverse=True)
            return results

    except Exception as e:
        print(f"Semantic similarity computation failed: {e}")
        return []


def find_similar_papers(query_text, papers, top_k=5, model=None):
    """
    Find papers most similar to the query text.
    
    Args:
        query_text: Text to find similar papers for.
        papers: List of paper dictionaries (must have 'abstract' or 'title' field).
        top_k: Number of similar papers to return.
        model: Pre-loaded SentenceTransformer model.
        
    Returns:
        List of papers with similarity scores added.
    """
    if not papers:
        return []

    # Build document list from abstracts
    documents = []
    for p in papers:
        text = p.get('abstract', '') or p.get('title', '')
        documents.append(text)

    # Compute semantic similarity
    results = compute_semantic_similarity(query_text, documents, model)

    # Map results back to papers
    similar_papers = []
    for idx, score in results[:top_k]:
        if 0 <= idx < len(papers):
            paper = papers[idx].copy()
            paper['similarity_score'] = round(score, 4)
            similar_papers.append(paper)

    return similar_papers


def extract_keywords(text, top_n=10):
    """
    Extract top keywords from text using TF-IDF.
    
    Args:
        text: Input text.
        top_n: Number of keywords to extract.
        
    Returns:
        List of (keyword, score) tuples.
    """
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        keyword_scores = list(zip(feature_names, scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)

        return keyword_scores[:top_n]

    except Exception as e:
        print(f"Keyword extraction failed: {e}")
        return []
