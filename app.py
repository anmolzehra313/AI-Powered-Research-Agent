"""
AI-Powered Research Agent Application

Main entry point for the Streamlit application.
Provides sidebar navigation to all research tool pages.

Run with: streamlit run app.py
"""

import streamlit as st
import os
import sys

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import page modules
from pages import search_papers
from pages import citation_extractor
from pages import related_work
from pages import plagiarism_checker
from pages import reference_formatter
from pages import pdf_processing
from pages import ai_chat
from pages import export_results


# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 10px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        font-weight: bold;
    }

    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1.1em;
        margin-bottom: 20px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: #e0e0e0;
    }

    /* Hide default Streamlit navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Card-like containers */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #888;
        font-size: 0.85em;
        border-top: 1px solid #eee;
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Sidebar Navigation ====================
with st.sidebar:
    st.markdown("## 🔬 AI Research Agent")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        [
            "🏠 Home",
            "🔍 Search Papers",
            "📚 Citation Extractor",
            "🔗 Related Work",
            "🔎 Plagiarism Checker",
            "📝 Reference Formatter",
            "📄 PDF Processing",
            "🤖 AI Chat",
            "📥 Export Results",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        "An AI-powered research assistant that automates literature search, "
        "citation management, plagiarism detection, and reference formatting."
    )
    st.markdown("---")
    st.caption("Built with Python & Streamlit")

# ==================== Page Routing ====================

if page == "🏠 Home":
    # Home page
    st.markdown('<h1 class="main-header">🔬 AI-Powered Research Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automate your research workflow with intelligent AI tools</p>',
                unsafe_allow_html=True)

    st.markdown("---")

    # Feature cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        ### 🔍 Paper Search
        Search across **Semantic Scholar**, **arXiv**, and **CrossRef** databases.
        Find papers by title, keyword, author, or DOI.
        """)

    with col2:
        st.markdown("""
        ### 📚 Citation Extraction
        Upload PDFs to **automatically extract** and parse references.
        Export as CSV for spreadsheet analysis.
        """)

    with col3:
        st.markdown("""
        ### 🔗 Related Work
        Find similar papers using **semantic embeddings** and **TF-IDF** analysis.
        Discover related topics.
        """)

    with col4:
        st.markdown("""
        ### 🔎 Plagiarism Detection
        Compare documents for similarity using **NLP** and **sentence transformers**.
        Get detailed reports.
        """)

    st.markdown("")

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown("""
        ### 📝 Reference Formatting
        Format references in **APA**, **IEEE**, **MLA**, or **Harvard** style automatically.
        """)

    with col6:
        st.markdown("""
        ### 📄 PDF Processing
        Extract **text**, **abstract**, **references**, and **metadata** from PDFs.
        """)

    with col7:
        st.markdown("""
        ### 🤖 AI Chat
        Chat with your papers. Ask questions, get **summaries**, and understand **methodologies**.
        """)

    with col8:
        st.markdown("""
        ### 📥 Export Results
        Export all your data in **CSV**, **PDF**, or **DOCX** format.
        """)

    st.markdown("---")

    # Quick start guide
    st.subheader("🚀 Quick Start")
    st.markdown("""
    1. **Search Papers** – Start by searching for research papers on any topic
    2. **Upload PDF** – Upload a research paper PDF for processing
    3. **Extract Citations** – Automatically extract and parse references
    4. **Chat with AI** – Ask questions about your uploaded papers
    5. **Export Results** – Download your results in multiple formats
    """)

    # Stats if available
    if any([
        'search_results' in st.session_state,
        'extracted_citations' in st.session_state,
        'chat_messages' in st.session_state,
    ]):
        st.markdown("---")
        st.subheader("📊 Session Statistics")
        stat_cols = st.columns(4)

        with stat_cols[0]:
            count = len(st.session_state.get('search_results', []))
            st.metric("Papers Found", count)

        with stat_cols[1]:
            count = len(st.session_state.get('extracted_citations', []))
            st.metric("Citations Extracted", count)

        with stat_cols[2]:
            score = st.session_state.get('plagiarism_result', {}).get('overall_plagiarism_score', '-')
            st.metric("Plagiarism Score", f"{score}%" if score != '-' else '-')

        with stat_cols[3]:
            count = len(st.session_state.get('chat_messages', []))
            st.metric("Chat Messages", count)

    st.markdown('<div class="footer">AI Research Agent © 2024 | Built for CEP Assignment</div>',
                unsafe_allow_html=True)

elif page == "🔍 Search Papers":
    search_papers.render()

elif page == "📚 Citation Extractor":
    citation_extractor.render()

elif page == "🔗 Related Work":
    related_work.render()

elif page == "🔎 Plagiarism Checker":
    plagiarism_checker.render()

elif page == "📝 Reference Formatter":
    reference_formatter.render()

elif page == "📄 PDF Processing":
    pdf_processing.render()

elif page == "🤖 AI Chat":
    ai_chat.render()

elif page == "📥 Export Results":
    export_results.render()
