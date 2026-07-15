"""
Research Paper Search Page

Search papers across Semantic Scholar, arXiv, and CrossRef APIs.
Display results with title, authors, abstract, year, citations, DOI, and PDF link.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.semantic_search import (
    search_semantic_scholar,
    search_arxiv,
    search_crossref,
    search_all_sources,
    find_similar_papers,
    extract_keywords,
)


def render():
    """Render the Research Paper Search page."""
    st.title("🔍 Research Paper Search")
    st.markdown("Search across **Semantic Scholar**, **arXiv**, and **CrossRef** databases.")

    # Search configuration
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="Enter title, keyword, author, or DOI...",
            help="Search papers by title, keyword, author name, or DOI",
        )

    with col2:
        search_source = st.selectbox(
            "Source",
            ["All Sources", "Semantic Scholar", "arXiv", "CrossRef"],
        )

    col3, col4 = st.columns([1, 1])
    with col3:
        num_results = st.slider("Results per source", 3, 20, 5)
    with col4:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    # Perform search
    if search_button and query:
        with st.spinner("Searching papers..."):
            papers = []

            if search_source == "All Sources":
                papers = search_all_sources(query, limit_per_source=num_results)
            elif search_source == "Semantic Scholar":
                papers = search_semantic_scholar(query, limit=num_results)
            elif search_source == "arXiv":
                papers = search_arxiv(query, limit=num_results)
            elif search_source == "CrossRef":
                papers = search_crossref(query, limit=num_results)

            if papers:
                st.session_state['search_results'] = papers
                st.success(f"Found {len(papers)} papers!")
            else:
                st.warning("No papers found. Try a different query or source.")

    # Display results
    if 'search_results' in st.session_state and st.session_state['search_results']:
        papers = st.session_state['search_results']

        st.markdown("---")
        st.subheader(f"📄 Search Results ({len(papers)} papers)")

        # Summary table
        summary_data = []
        for p in papers:
            summary_data.append({
                'Title': p['title'][:80] + '...' if len(p.get('title', '')) > 80 else p.get('title', 'N/A'),
                'Year': p.get('year', 'N/A'),
                'Citations': p.get('citation_count', 'N/A'),
                'Source': p.get('source', 'N/A'),
            })

        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

        # Detailed paper cards
        st.markdown("### 📋 Detailed Results")

        for i, paper in enumerate(papers):
            with st.expander(f"📄 {paper.get('title', 'Untitled')}", expanded=(i == 0)):
                col_a, col_b = st.columns([3, 1])

                with col_a:
                    st.markdown(f"**Authors:** {paper.get('authors', 'N/A')}")
                    st.markdown(f"**Year:** {paper.get('year', 'N/A')} | "
                                f"**Citations:** {paper.get('citation_count', 'N/A')} | "
                                f"**Source:** {paper.get('source', 'N/A')}")

                with col_b:
                    if paper.get('doi'):
                        st.markdown(f"**DOI:** `{paper['doi']}`")
                    if paper.get('pdf_url'):
                        st.link_button("📥 PDF", paper['pdf_url'])

                # Abstract
                abstract = paper.get('abstract', 'No abstract available')
                if abstract and abstract != 'No abstract available':
                    st.markdown("**Abstract:**")
                    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; "
                                f"border-radius: 5px; font-size: 14px;'>{abstract}</div>",
                                unsafe_allow_html=True)
                else:
                    st.info("Abstract not available.")

                if paper.get('url'):
                    st.link_button("🔗 View Paper", paper['url'])

        # Similar papers suggestion
        st.markdown("---")
        st.subheader("💡 Find Similar Papers")

        selected_idx = st.selectbox(
            "Select a paper to find similar ones:",
            range(len(papers)),
            format_func=lambda i: papers[i]['title'][:80],
        )

        if st.button("Find Similar Papers"):
            with st.spinner("Finding similar papers..."):
                selected_paper = papers[selected_idx]
                query_text = f"{selected_paper.get('title', '')} {selected_paper.get('abstract', '')}"

                # Search for more papers to compare against
                more_papers = search_all_sources(
                    selected_paper['title'][:50], limit_per_source=5
                )

                if more_papers:
                    similar = find_similar_papers(query_text, more_papers, top_k=5)
                    if similar:
                        st.success(f"Found {len(similar)} similar papers!")
                        for sim_paper in similar:
                            score = sim_paper.get('similarity_score', 0)
                            st.markdown(f"**{sim_paper['title']}** (Similarity: {score:.2%})")
                            st.caption(f"Authors: {sim_paper.get('authors', 'N/A')} | "
                                       f"Year: {sim_paper.get('year', 'N/A')} | "
                                       f"Source: {sim_paper.get('source', 'N/A')}")
                    else:
                        st.info("Could not find similar papers.")
                else:
                    st.info("No additional papers found for comparison.")

        # Keywords extraction
        st.markdown("---")
        st.subheader("🏷️ Extract Keywords")
        if st.button("Extract Keywords from Results"):
            combined_text = ' '.join([
                f"{p.get('title', '')} {p.get('abstract', '')}" for p in papers
            ])
            keywords = extract_keywords(combined_text, top_n=15)
            if keywords:
                keyword_df = pd.DataFrame(keywords, columns=['Keyword', 'Score'])
                keyword_df['Score'] = keyword_df['Score'].round(4)
                st.dataframe(keyword_df, use_container_width=True, hide_index=True)
