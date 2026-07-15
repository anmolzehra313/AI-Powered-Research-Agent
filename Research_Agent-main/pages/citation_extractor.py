"""
Citation Extractor Page

Upload PDF research papers to extract references automatically.
Detect citation section, extract author names, title, journal, year, and DOI.
Export citations as CSV or BibTeX.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.pdf_processor import extract_text_from_pdf, extract_references_section
from utils.citation_utils import (
    parse_references_from_text,
    citations_to_dataframe,
    citations_to_csv,
)


def render():
    """Render the Citation Extractor page."""
    st.title("📚 Citation Extractor")
    st.markdown("Upload a PDF research paper to automatically extract and parse references.")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload a PDF research paper",
        type=['pdf'],
        help="Upload a PDF file to extract citations from its references section.",
    )

    # Manual text input option
    with st.expander("📝 Or paste reference text manually"):
        manual_refs = st.text_area(
            "Paste references text here:",
            height=200,
            placeholder="[1] Author A, Author B. Title of paper. Journal Name, vol. 1, pp. 1-10, 2023.\n[2] ...",
        )

    citations = []

    if uploaded_file is not None:
        with st.spinner("Processing PDF..."):
            # Read PDF
            pdf_bytes = uploaded_file.read()
            text = extract_text_from_pdf(pdf_bytes)

            if text:
                st.success(f"✅ PDF processed successfully! ({len(text)} characters extracted)")

                # Extract references section
                refs_text = extract_references_section(text)

                if refs_text:
                    st.markdown("### 📖 Extracted References Section")
                    with st.expander("View raw references text", expanded=False):
                        st.text(refs_text[:3000])

                    # Parse references
                    citations = parse_references_from_text(refs_text)

                    if citations:
                        st.session_state['extracted_citations'] = citations
                        st.success(f"✅ Found {len(citations)} references!")
                    else:
                        st.warning("Could not parse individual references. The format may be non-standard.")
                else:
                    st.warning("Could not locate the references section in this PDF. "
                               "Try pasting references manually below.")
            else:
                st.error("Failed to extract text from the PDF. The file may be scanned or corrupted.")

    elif manual_refs:
        citations = parse_references_from_text(manual_refs)
        if citations:
            st.session_state['extracted_citations'] = citations
            st.success(f"✅ Parsed {len(citations)} references!")
        else:
            st.warning("Could not parse the provided references text.")

    # Display parsed citations
    if 'extracted_citations' in st.session_state and st.session_state['extracted_citations']:
        citations = st.session_state['extracted_citations']

        st.markdown("---")
        st.subheader(f"📋 Parsed Citations ({len(citations)})")

        # Display as table
        df = citations_to_dataframe(citations)
        if not df.empty:
            # Show editable table (display only, not truly editable)
            display_cols = [c for c in ['authors', 'title', 'journal', 'year', 'doi'] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        # Individual citation cards
        st.markdown("### 📄 Citation Details")
        for i, citation in enumerate(citations):
            with st.expander(f"Reference {i + 1}: {citation.get('title', 'Unknown')[:60]}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Authors:** {citation.get('authors', 'N/A')}")
                    st.markdown(f"**Title:** {citation.get('title', 'N/A')}")
                    st.markdown(f"**Journal:** {citation.get('journal', 'N/A')}")
                with col2:
                    st.markdown(f"**Year:** {citation.get('year', 'N/A')}")
                    st.markdown(f"**Volume:** {citation.get('volume', 'N/A')}")
                    st.markdown(f"**Pages:** {citation.get('pages', 'N/A')}")
                    st.markdown(f"**DOI:** {citation.get('doi', 'N/A')}")

                st.caption(f"Raw: {citation.get('raw', '')[:200]}")

        # Export options
        st.markdown("---")
        st.subheader("📥 Export Citations")

        # CSV export
        csv_data = citations_to_csv(citations)
        st.download_button(
            "📥 Download as CSV",
            data=csv_data,
            file_name="extracted_citations.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Store for export page
        st.session_state['citations_csv'] = csv_data

    # Clear button
    if st.button("🗑️ Clear Results"):
        if 'extracted_citations' in st.session_state:
            del st.session_state['extracted_citations']
        st.rerun()
