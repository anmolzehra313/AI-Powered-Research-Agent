"""
Reference Formatter Page

Format references in APA, IEEE, MLA, and Harvard styles.
Supports manual input, batch formatting, and BibTeX export.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.reference_utils import (
    format_reference,
    format_references_batch,
    generate_bibtex,
    generate_bibtex_batch,
)


def render():
    """Render the Reference Formatter page."""
    st.title("📝 Automatic Reference Formatting")
    st.markdown("Format your references in **APA**, **IEEE**, **MLA**, or **Harvard** style automatically.")

    # Formatting style selection
    style = st.selectbox(
        "Select Citation Style",
        ["APA", "IEEE", "MLA", "Harvard"],
        help="Choose the citation formatting style.",
    )

    st.markdown("---")

    # Tabs for single and batch formatting
    tab1, tab2, tab3 = st.tabs(["📄 Single Reference", "📋 Batch Formatting", "📥 From Extracted Citations"])

    with tab1:
        st.markdown("### Enter Reference Details")

        col1, col2 = st.columns(2)
        with col1:
            authors = st.text_input(
                "Authors",
                placeholder="John Smith, Jane Doe",
                help="Comma-separated author names (First Last format)",
            )
            title = st.text_input(
                "Title",
                placeholder="A Study on Machine Learning Approaches",
            )
            journal = st.text_input(
                "Journal / Conference",
                placeholder="IEEE Transactions on Neural Networks",
            )

        with col2:
            year = st.text_input("Year", placeholder="2023")
            volume = st.text_input("Volume", placeholder="15")
            issue = st.text_input("Issue", placeholder="3")
            pages = st.text_input("Pages", placeholder="101-115")
            doi = st.text_input("DOI", placeholder="10.1109/TNN.2023.12345")

        if st.button("📝 Format Reference", type="primary"):
            if title:  # Minimum required field
                reference = {
                    'authors': authors,
                    'title': title,
                    'journal': journal,
                    'year': year,
                    'volume': volume,
                    'issue': issue,
                    'pages': pages,
                    'doi': doi,
                }

                formatted = format_reference(reference, style.lower())
                bibtex = generate_bibtex(reference)

                st.markdown("### ✅ Formatted Reference")
                st.markdown(
                    f"<div style='background-color: #e8f4f8; padding: 15px; "
                    f"border-left: 4px solid #2196F3; border-radius: 5px; "
                    f"font-size: 15px;'>{formatted}</div>",
                    unsafe_allow_html=True,
                )

                # Copy-friendly version
                st.code(formatted, language=None)

                st.markdown("### 📑 BibTeX")
                st.code(bibtex, language="bibtex")

                # Store for export
                if 'formatted_references' not in st.session_state:
                    st.session_state['formatted_references'] = []
                st.session_state['formatted_references'].append({
                    'reference': reference,
                    'formatted': formatted,
                    'style': style,
                })
            else:
                st.warning("Please enter at least a title.")

    with tab2:
        st.markdown("### Batch Reference Formatting")
        st.markdown("Add multiple references and format them all at once.")

        # Number of references
        num_refs = st.number_input("Number of references", 1, 20, 3)

        references = []
        for i in range(num_refs):
            with st.expander(f"Reference {i + 1}", expanded=(i < 2)):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    r_authors = st.text_input("Authors", key=f"batch_auth_{i}", placeholder="Author names")
                    r_title = st.text_input("Title", key=f"batch_title_{i}", placeholder="Paper title")
                    r_journal = st.text_input("Journal", key=f"batch_journal_{i}", placeholder="Journal name")
                with r_col2:
                    r_year = st.text_input("Year", key=f"batch_year_{i}", placeholder="2023")
                    r_volume = st.text_input("Volume", key=f"batch_vol_{i}", placeholder="")
                    r_pages = st.text_input("Pages", key=f"batch_pages_{i}", placeholder="")
                    r_doi = st.text_input("DOI", key=f"batch_doi_{i}", placeholder="")

                references.append({
                    'authors': r_authors, 'title': r_title, 'journal': r_journal,
                    'year': r_year, 'volume': r_volume, 'issue': '',
                    'pages': r_pages, 'doi': r_doi,
                })

        if st.button("📝 Format All References", type="primary"):
            valid_refs = [r for r in references if r.get('title')]
            if valid_refs:
                formatted_list = format_references_batch(valid_refs, style.lower())
                bibtex_all = generate_bibtex_batch(valid_refs)

                st.markdown(f"### ✅ Formatted References ({style})")
                for i, formatted in enumerate(formatted_list):
                    st.markdown(
                        f"<div style='background-color: #e8f4f8; padding: 10px; "
                        f"border-left: 4px solid #2196F3; border-radius: 5px; "
                        f"margin-bottom: 8px; font-size: 14px;'>{formatted}</div>",
                        unsafe_allow_html=True,
                    )

                # Export options
                st.markdown("### 📥 Export")
                col_a, col_b = st.columns(2)
                with col_a:
                    all_formatted_text = '\n\n'.join(formatted_list)
                    st.download_button(
                        f"📥 Download {style} References",
                        data=all_formatted_text,
                        file_name=f"references_{style.lower()}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with col_b:
                    st.download_button(
                        "📥 Download BibTeX",
                        data=bibtex_all,
                        file_name="references.bib",
                        mime="text/plain",
                        use_container_width=True,
                    )

                st.session_state['batch_formatted'] = all_formatted_text
                st.session_state['batch_bibtex'] = bibtex_all
            else:
                st.warning("Please fill in at least one reference (title is required).")

    with tab3:
        st.markdown("### Format Extracted Citations")
        st.markdown("Use citations previously extracted from a PDF on the Citation Extractor page.")

        if 'extracted_citations' in st.session_state and st.session_state['extracted_citations']:
            citations = st.session_state['extracted_citations']
            st.info(f"Found {len(citations)} extracted citations from Citation Extractor.")

            if st.button("📝 Format Extracted Citations", type="primary"):
                # Convert citation format
                refs = []
                for c in citations:
                    refs.append({
                        'authors': c.get('authors', ''),
                        'title': c.get('title', ''),
                        'journal': c.get('journal', ''),
                        'year': c.get('year', ''),
                        'volume': c.get('volume', ''),
                        'issue': '',
                        'pages': c.get('pages', ''),
                        'doi': c.get('doi', ''),
                    })

                formatted_list = format_references_batch(refs, style.lower())
                bibtex_all = generate_bibtex_batch(refs)

                st.markdown(f"### ✅ Formatted ({style})")
                for formatted in formatted_list:
                    st.markdown(
                        f"<div style='background-color: #e8f4f8; padding: 10px; "
                        f"border-left: 4px solid #2196F3; border-radius: 5px; "
                        f"margin-bottom: 8px; font-size: 14px;'>{formatted}</div>",
                        unsafe_allow_html=True,
                    )

                # Export
                col_a, col_b = st.columns(2)
                with col_a:
                    all_text = '\n\n'.join(formatted_list)
                    st.download_button(
                        f"📥 Download {style}",
                        data=all_text,
                        file_name=f"formatted_refs_{style.lower()}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with col_b:
                    st.download_button(
                        "📥 Download BibTeX",
                        data=bibtex_all,
                        file_name="formatted_refs.bib",
                        mime="text/plain",
                        use_container_width=True,
                    )
        else:
            st.info("No extracted citations found. Go to the **Citation Extractor** page first to upload a PDF and extract citations.")
