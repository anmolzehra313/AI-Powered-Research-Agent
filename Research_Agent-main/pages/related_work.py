"""
Related Work Suggestion Page

Recommend similar papers using Sentence Transformers and TF-IDF.
Display similarity scores and suggest related topics.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.pdf_processor import extract_text_from_pdf, extract_abstract
from utils.semantic_search import (
    search_all_sources,
    find_similar_papers,
    compute_tfidf_similarity,
    extract_keywords,
)


def render():
    """Render the Related Work Suggestion page."""
    st.title("🔗 Related Work Suggestions")
    st.markdown("Find similar papers and related topics using **semantic embeddings** and **TF-IDF** analysis.")

    # Input method selection
    input_method = st.radio(
        "Input Method",
        ["Text Input", "PDF Upload"],
        horizontal=True,
    )

    query_text = ""

    if input_method == "Text Input":
        query_text = st.text_area(
            "Enter your research text, abstract, or topic:",
            height=200,
            placeholder="Paste your abstract, research description, or topic keywords here...",
        )
    else:
        uploaded_file = st.file_uploader("Upload a PDF research paper", type=['pdf'])
        if uploaded_file:
            with st.spinner("Extracting text from PDF..."):
                pdf_bytes = uploaded_file.read()
                full_text = extract_text_from_pdf(pdf_bytes)
                if full_text:
                    abstract = extract_abstract(full_text)
                    query_text = abstract
                    st.success("✅ PDF processed! Using extracted abstract for search.")
                    with st.expander("View extracted abstract"):
                        st.write(abstract)
                else:
                    st.error("Failed to extract text from PDF.")

    # Search parameters
    col1, col2 = st.columns(2)
    with col1:
        num_results = st.slider("Number of recommendations", 3, 20, 10)
    with col2:
        min_similarity = st.slider("Minimum similarity score", 0.0, 1.0, 0.1, 0.05)

    # Find related work
    if st.button("🔍 Find Related Work", type="primary") and query_text:
        with st.spinner("Searching for related papers..."):
            # Extract keywords for targeted search
            keywords = extract_keywords(query_text, top_n=5)
            search_queries = [query_text[:100]]

            if keywords:
                keyword_text = ' '.join([kw[0] for kw in keywords[:3]])
                search_queries.append(keyword_text)

            # Search across all sources
            all_papers = []
            for sq in search_queries:
                papers = search_all_sources(sq, limit_per_source=num_results)
                all_papers.extend(papers)

            # Remove duplicates by title
            seen_titles = set()
            unique_papers = []
            for p in all_papers:
                title_lower = p.get('title', '').lower().strip()
                if title_lower and title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    unique_papers.append(p)

            if unique_papers:
                # Find similar papers using semantic similarity
                similar = find_similar_papers(
                    query_text, unique_papers, top_k=num_results
                )

                # Filter by minimum similarity
                similar = [p for p in similar if p.get('similarity_score', 0) >= min_similarity]

                if similar:
                    st.session_state['related_papers'] = similar
                    st.success(f"Found {len(similar)} related papers!")
                else:
                    st.warning(f"No papers found with similarity ≥ {min_similarity:.0%}. Try lowering the threshold.")
            else:
                st.warning("No papers found. Try different keywords or text.")

    # Display results
    if 'related_papers' in st.session_state and st.session_state['related_papers']:
        similar = st.session_state['related_papers']

        st.markdown("---")
        st.subheader(f"📄 Related Papers ({len(similar)})")

        # Summary table with similarity scores
        summary_data = []
        for p in similar:
            summary_data.append({
                'Title': p['title'][:70] + '...' if len(p.get('title', '')) > 70 else p.get('title', ''),
                'Similarity': f"{p.get('similarity_score', 0):.2%}",
                'Year': p.get('year', 'N/A'),
                'Source': p.get('source', 'N/A'),
            })

        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

        # Detailed cards
        for i, paper in enumerate(similar):
            score = paper.get('similarity_score', 0)
            # Color based on similarity
            if score >= 0.8:
                color = "🟢"
            elif score >= 0.5:
                color = "🟡"
            else:
                color = "🔴"

            with st.expander(
                f"{color} {paper['title'][:80]} (Similarity: {score:.2%})",
                expanded=(i < 3),
            ):
                st.markdown(f"**Authors:** {paper.get('authors', 'N/A')}")
                st.markdown(f"**Year:** {paper.get('year', 'N/A')} | "
                            f"**Citations:** {paper.get('citation_count', 'N/A')} | "
                            f"**Source:** {paper.get('source', 'N/A')}")

                abstract = paper.get('abstract', '')
                if abstract and abstract != 'No abstract available':
                    st.markdown("**Abstract:**")
                    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; "
                                f"border-radius: 5px; font-size: 14px;'>{abstract[:500]}...</div>",
                                unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    if paper.get('doi'):
                        st.markdown(f"**DOI:** `{paper['doi']}`")
                with col_b:
                    if paper.get('url'):
                        st.link_button("🔗 View Paper", paper['url'])

        # Related Topics
        if query_text:
            st.markdown("---")
            st.subheader("🏷️ Suggested Related Topics")

            # Extract keywords from results
            combined_text = ' '.join([
                f"{p.get('title', '')} {p.get('abstract', '')}" for p in similar
            ])
            topics = extract_keywords(combined_text, top_n=10)

            if topics:
                cols = st.columns(5)
                for i, (topic, score) in enumerate(topics):
                    with cols[i % 5]:
                        st.markdown(
                            f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
                            f"color: white; padding: 8px 12px; border-radius: 20px; "
                            f"text-align: center; margin: 4px 0; font-size: 13px;'>"
                            f"{topic}</div>",
                            unsafe_allow_html=True,
                        )
