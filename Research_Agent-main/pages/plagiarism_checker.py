"""
Plagiarism Checker Page

Detect similarity between texts or uploaded PDFs using NLP techniques.
Shows similarity percentage, highlights matching sentences, and generates reports.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.pdf_processor import extract_text_from_pdf
from utils.plagiarism_utils import (
    calculate_plagiarism_percentage,
    generate_plagiarism_report,
    highlight_matching_text,
)


def render():
    """Render the Plagiarism Checker page."""
    st.title("🔎 Plagiarism Detection")
    st.markdown("Compare two texts or documents for similarity using **cosine similarity**, "
                "**sentence transformers**, and **NLP comparison**.")

    # Input method
    input_method = st.radio(
        "Input Method",
        ["Text Input", "PDF Upload"],
        horizontal=True,
    )

    text1 = ""
    text2 = ""

    if input_method == "Text Input":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📄 Document 1 (Source)")
            text1 = st.text_area(
                "Enter source text:",
                height=250,
                placeholder="Paste the source/original document text here...",
                key="plag_text1",
            )
        with col2:
            st.markdown("#### 📄 Document 2 (Comparison)")
            text2 = st.text_area(
                "Enter comparison text:",
                height=250,
                placeholder="Paste the comparison document text here...",
                key="plag_text2",
            )
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📄 Document 1 (Source)")
            file1 = st.file_uploader("Upload source PDF", type=['pdf'], key="plag_file1")
            if file1:
                pdf_bytes1 = file1.read()
                text1 = extract_text_from_pdf(pdf_bytes1)
                if text1:
                    st.success(f"✅ Extracted {len(text1)} characters")
                else:
                    st.error("Failed to extract text from PDF 1.")
        with col2:
            st.markdown("#### 📄 Document 2 (Comparison)")
            file2 = st.file_uploader("Upload comparison PDF", type=['pdf'], key="plag_file2")
            if file2:
                pdf_bytes2 = file2.read()
                text2 = extract_text_from_pdf(pdf_bytes2)
                if text2:
                    st.success(f"✅ Extracted {len(text2)} characters")
                else:
                    st.error("Failed to extract text from PDF 2.")

    # Detection settings
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        threshold = st.slider(
            "Sentence matching threshold",
            0.3, 1.0, 0.7, 0.05,
            help="Minimum similarity score for two sentences to be considered matching.",
        )
    with col_b:
        st.info("💡 Lower threshold = more matches detected. Higher = stricter matching.")

    # Run plagiarism check
    if st.button("🔍 Check Plagiarism", type="primary") and text1 and text2:
        with st.spinner("Analyzing documents for similarity... This may take a moment."):
            try:
                result = calculate_plagiarism_percentage(text1, text2)
                st.session_state['plagiarism_result'] = result
                st.session_state['plag_text1'] = text1
                st.session_state['plag_text2'] = text2
            except Exception as e:
                st.error(f"Error during plagiarism detection: {str(e)}")

    # Display results
    if 'plagiarism_result' in st.session_state:
        result = st.session_state['plagiarism_result']

        st.markdown("---")
        st.subheader("📊 Plagiarism Detection Results")

        # Overall score with visual indicator
        overall_score = result['overall_plagiarism_score']

        if overall_score >= 60:
            score_color = "🔴"
            status = "High Similarity"
            bar_color = "red"
        elif overall_score >= 30:
            score_color = "🟡"
            status = "Moderate Similarity"
            bar_color = "orange"
        else:
            score_color = "🟢"
            status = "Low Similarity"
            bar_color = "green"

        st.markdown(
            f"<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); "
            f"border-radius: 10px; margin: 10px 0;'>"
            f"<h1 style='color: {bar_color}; margin: 0;'>{score_color} {overall_score}%</h1>"
            f"<p style='color: #aaa; font-size: 18px;'>{status}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Detailed scores
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("TF-IDF Similarity", f"{result['tfidf_similarity']}%")
        with col2:
            st.metric("Semantic Similarity", f"{result['semantic_similarity']}%")
        with col3:
            st.metric("Sentence Match Ratio", f"{result['sentence_match_ratio']}%")

        st.markdown(f"**Total Source Sentences:** {result['total_source_sentences']} | "
                    f"**Matched Sentences:** {result['matched_sentence_count']}")

        # Matching sentences
        matches = result.get('matching_sentences', [])
        if matches:
            st.markdown("---")
            st.subheader(f"🔍 Matching Sentences ({len(matches)})")

            match_data = []
            for m in matches:
                match_data.append({
                    'Source Sentence': m['source_sentence'][:80] + '...'
                    if len(m['source_sentence']) > 80 else m['source_sentence'],
                    'Matching Sentence': m['matching_sentence'][:80] + '...'
                    if len(m['matching_sentence']) > 80 else m['matching_sentence'],
                    'Similarity': f"{m['similarity_score']*100:.1f}%",
                })

            st.dataframe(pd.DataFrame(match_data), use_container_width=True, hide_index=True)

            # Highlighted text view
            st.markdown("---")
            st.subheader("🖍️ Highlighted Matching Text")

            tab1, tab2 = st.tabs(["Document 1 (Source)", "Document 2 (Comparison)"])

            with tab1:
                source_text = st.session_state.get('plag_text1', text1)
                highlighted_source = highlight_matching_text(source_text, matches, role='source')
                st.markdown(f'<div style="font-size: 14px; line-height: 1.6; color: #e0e0e0; text-align: justify;">{highlighted_source}</div>', unsafe_allow_html=True)

            with tab2:
                comp_text = st.session_state.get('plag_text2', text2)
                highlighted_comp = highlight_matching_text(comp_text, matches, role='target')
                st.markdown(f'<div style="font-size: 14px; line-height: 1.6; color: #e0e0e0; text-align: justify;">{highlighted_comp}</div>', unsafe_allow_html=True)

        else:
            st.info("No matching sentences found above the threshold.")

        # Generate and download report
        st.markdown("---")
        st.subheader("📥 Download Report")

        report_text = generate_plagiarism_report(result)
        st.session_state['plagiarism_report'] = report_text

        st.download_button(
            "📥 Download Plagiarism Report",
            data=report_text,
            file_name="plagiarism_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Clear button
    if st.button("🗑️ Clear Results"):
        for key in ['plagiarism_result', 'plag_text1', 'plag_text2', 'plagiarism_report']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
