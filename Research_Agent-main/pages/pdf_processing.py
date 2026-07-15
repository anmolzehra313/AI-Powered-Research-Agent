"""
PDF Processing Page

Upload and process PDF research papers.
Extract text, abstract, references, and metadata.
Split text into chunks for analysis.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.pdf_processor import (
    extract_text_from_pdf,
    extract_abstract,
    extract_references_section,
    extract_metadata,
    chunk_text,
    get_page_count,
    extract_text_by_page,
)


def render():
    """Render the PDF Processing page."""
    st.title("📄 PDF Upload & Processing")
    st.markdown("Upload PDF research papers to extract text, abstract, references, and metadata.")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload a PDF research paper",
        type=['pdf'],
        help="Upload a PDF file to process and analyze.",
    )

    if uploaded_file is not None:
        pdf_bytes = uploaded_file.read()

        with st.spinner("Processing PDF..."):
            # Extract metadata
            metadata = extract_metadata(pdf_bytes)

            # Extract full text
            full_text = extract_text_from_pdf(pdf_bytes)

            if not full_text:
                st.error("❌ Failed to extract text from the PDF. The file may be scanned or corrupted.")
                return

            # Extract abstract
            abstract = extract_abstract(full_text)

            # Extract references
            references_text = extract_references_section(full_text)

            # Get page-by-page text
            pages = extract_text_by_page(pdf_bytes)

        st.success(f"✅ PDF processed successfully!")

        # Store in session state for other pages
        st.session_state['pdf_full_text'] = full_text
        st.session_state['pdf_abstract'] = abstract
        st.session_state['pdf_metadata'] = metadata
        st.session_state['pdf_references'] = references_text

        # Metadata display
        st.markdown("---")
        st.subheader("📋 Document Metadata")

        if metadata:
            meta_cols = st.columns(3)
            with meta_cols[0]:
                st.markdown(f"**Title:** {metadata.get('title', 'N/A') or 'N/A'}")
                st.markdown(f"**Author:** {metadata.get('author', 'N/A') or 'N/A'}")
            with meta_cols[1]:
                st.markdown(f"**Subject:** {metadata.get('subject', 'N/A') or 'N/A'}")
                st.markdown(f"**Keywords:** {metadata.get('keywords', 'N/A') or 'N/A'}")
            with meta_cols[2]:
                st.markdown(f"**Pages:** {metadata.get('page_count', 'N/A')}")
                st.markdown(f"**Characters:** {len(full_text):,}")
                st.markdown(f"**Words:** {len(full_text.split()):,}")

        # Document sections
        st.markdown("---")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Full Text", "📜 Abstract", "📚 References", "📄 Page View", "🧩 Text Chunks"
        ])

        with tab1:
            st.subheader("Full Extracted Text")
            st.markdown(f"*{len(full_text):,} characters / {len(full_text.split()):,} words*")
            st.text_area(
                "Full text:",
                value=full_text[:10000],
                height=400,
                disabled=True,
                label_visibility="collapsed",
            )
            if len(full_text) > 10000:
                st.caption(f"Showing first 10,000 of {len(full_text):,} characters.")

            st.download_button(
                "📥 Download Full Text",
                data=full_text,
                file_name="extracted_text.txt",
                mime="text/plain",
            )

        with tab2:
            st.subheader("Extracted Abstract")
            if abstract:
                st.markdown(
                    f"<div style='background-color: #1e293b; color: white; padding: 20px; "
                    f"border-left: 5px solid #667eea; border-radius: 8px; line-height: 1.6; "
                    f"font-size: 15px; text-align: justify;'>"
                    f"{abstract}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("Could not extract abstract from this document.")

        with tab3:
            st.subheader("Extracted References Section")
            if references_text:
                st.text_area(
                    "References:",
                    value=references_text[:5000],
                    height=300,
                    disabled=True,
                    label_visibility="collapsed",
                )
                st.caption("💡 Go to **Citation Extractor** page to parse these into structured citations.")
            else:
                st.info("Could not locate the references section in this document.")

        with tab4:
            st.subheader("Page-by-Page View")
            if pages:
                page_num = st.select_slider(
                    "Select page:",
                    options=[p[0] for p in pages],
                    value=pages[0][0],
                )
                for pn, pt in pages:
                    if pn == page_num:
                        st.text_area(
                            f"Page {pn}:",
                            value=pt,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed",
                        )
                        break
            else:
                st.info("Page-by-page extraction not available.")

        with tab5:
            st.subheader("Text Chunking")
            st.markdown("Split the document into chunks for embedding and retrieval.")

            col_a, col_b = st.columns(2)
            with col_a:
                chunk_size = st.number_input("Chunk size (words)", 100, 2000, 500, 50)
            with col_b:
                chunk_overlap = st.number_input("Overlap (words)", 0, 500, 50, 10)

            if st.button("🧩 Generate Chunks"):
                chunks = chunk_text(full_text, chunk_size=chunk_size, overlap=chunk_overlap)
                st.session_state['pdf_chunks'] = chunks
                st.success(f"Generated {len(chunks)} chunks!")

                # Display chunk info
                chunk_info = []
                for i, chunk in enumerate(chunks):
                    chunk_info.append({
                        'Chunk': i + 1,
                        'Words': len(chunk.split()),
                        'Characters': len(chunk),
                        'Preview': chunk[:100] + '...',
                    })

                st.dataframe(pd.DataFrame(chunk_info), use_container_width=True, hide_index=True)

                # View individual chunks
                chunk_idx = st.selectbox("View chunk:", range(len(chunks)),
                                         format_func=lambda i: f"Chunk {i+1}")
                st.text_area(
                    f"Chunk {chunk_idx + 1}:",
                    value=chunks[chunk_idx],
                    height=200,
                    disabled=True,
                    label_visibility="collapsed",
                )

                st.caption("💡 These chunks can be used with the **AI Chat** page for question answering.")
