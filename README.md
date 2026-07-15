# AI-Powered Research Agent

An intelligent research automation tool built with Python and Streamlit for academic researchers. Automates literature search, citation management, plagiarism detection, and reference formatting.

## Features

1. **Research Paper Search** – Search across Semantic Scholar, arXiv, and CrossRef APIs
2. **Citation Extraction** – Extract references from uploaded PDFs
3. **Related Work Suggestion** – Find similar papers using semantic embeddings
4. **Plagiarism Detection** – Compare texts using cosine similarity and NLP
5. **Reference Formatting** – Auto-format references in APA, IEEE, MLA, Harvard
6. **PDF Processing** – Extract text, abstract, and metadata from PDFs
7. **AI Research Assistant** – Chat with your papers using local LLM
8. **Export Results** – Export data as CSV, PDF, DOCX, or BibTeX

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data (first run only)
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords')"

# Run the application
streamlit run app.py
```

## Project Structure

```
research_agent/
├── app.py                  # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md
├── pages/                  # Streamlit page modules
│   ├── search_papers.py
│   ├── citation_extractor.py
│   ├── related_work.py
│   ├── plagiarism_checker.py
│   ├── reference_formatter.py
│   ├── pdf_processing.py
│   ├── ai_chat.py
│   └── export_results.py
├── utils/                  # Utility modules
│   ├── pdf_processor.py
│   ├── citation_utils.py
│   ├── plagiarism_utils.py
│   ├── semantic_search.py
│   ├── reference_utils.py
│   └── llm_utils.py
├── data/                   # Data storage
└── exports/                # Export output directory
```

## Technologies

- **Frontend**: Streamlit
- **NLP**: Sentence Transformers, NLTK, Transformers
- **Search**: FAISS, TF-IDF, Cosine Similarity
- **PDF**: PyMuPDF, pdfplumber, PyPDF2
- **AI**: LangChain, HuggingFace Transformers
- **APIs**: Semantic Scholar, arXiv, CrossRef

## Notes

- The AI chat feature uses a local HuggingFace model (`google/flan-t5-small`) by default — no API key required.
- Optionally enter an OpenAI API key in the sidebar for enhanced AI responses.
- API rate limits apply for paper search (Semantic Scholar, arXiv, CrossRef).
