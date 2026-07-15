"""
AI Research Assistant Chat Page

Chat with uploaded research papers using LangChain and local LLM.
Supports summarization, methodology explanation, and question answering.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.pdf_processor import extract_text_from_pdf, chunk_text, extract_abstract
from utils.llm_utils import (
    build_vector_store,
    search_vector_store,
    answer_question_local,
    answer_question_openai,
    summarize_paper,
    explain_methodology,
    extractive_summarize,
)


def render():
    """Render the AI Research Assistant Chat page."""
    st.title("🤖 AI Research Assistant")
    st.markdown("Chat with your research papers. Upload a PDF and ask questions about it.")

    # Sidebar configuration for API key
    with st.sidebar:
        st.markdown("### 🔑 AI Settings")
        api_key = st.text_input(
            "OpenAI API Key (optional)",
            type="password",
            help="Enter your OpenAI API key for enhanced responses. Leave blank to use local model.",
        )
        if api_key:
            st.session_state['openai_api_key'] = api_key
            st.success("✅ OpenAI API key set!")
        else:
            st.info("Using local model (flan-t5-small)")

    # Document upload
    st.markdown("### 📄 Upload Document")

    # Check if text is already available from PDF Processing page
    has_existing = 'pdf_full_text' in st.session_state and st.session_state['pdf_full_text']

    if has_existing:
        st.info("📄 A document is already loaded from the PDF Processing page. You can use it or upload a new one.")
        use_existing = st.checkbox("Use previously loaded document", value=True)
    else:
        use_existing = False

    uploaded_file = None
    if not use_existing:
        uploaded_file = st.file_uploader(
            "Upload a PDF research paper",
            type=['pdf'],
            key="ai_chat_pdf",
        )

    # Process document and build vector store
    if uploaded_file is not None:
        with st.spinner("Processing document and building knowledge base..."):
            pdf_bytes = uploaded_file.read()
            full_text = extract_text_from_pdf(pdf_bytes)

            if full_text:
                st.session_state['chat_full_text'] = full_text
                chunks = chunk_text(full_text, chunk_size=300, overlap=30)
                st.session_state['chat_chunks'] = chunks

                # Build vector store
                vector_store = build_vector_store(chunks)
                st.session_state['chat_vector_store'] = vector_store

                st.success(f"✅ Document processed! ({len(chunks)} chunks indexed)")
            else:
                st.error("Failed to extract text from the PDF.")

    elif use_existing and has_existing:
        if 'chat_vector_store' not in st.session_state:
            with st.spinner("Building knowledge base from existing document..."):
                full_text = st.session_state['pdf_full_text']
                st.session_state['chat_full_text'] = full_text
                chunks = chunk_text(full_text, chunk_size=300, overlap=30)
                st.session_state['chat_chunks'] = chunks

                vector_store = build_vector_store(chunks)
                st.session_state['chat_vector_store'] = vector_store
                st.success(f"✅ Knowledge base built! ({len(chunks)} chunks indexed)")

    # Quick action buttons
    if 'chat_full_text' in st.session_state:
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Summarize Paper", use_container_width=True):
                with st.spinner("Generating summary..."):
                    text = st.session_state['chat_full_text']
                    summary = summarize_paper(text)
                    _add_message("assistant", f"**📝 Paper Summary:**\n\n{summary}")

        with col2:
            if st.button("🔬 Explain Methodology", use_container_width=True):
                with st.spinner("Analyzing methodology..."):
                    text = st.session_state['chat_full_text']
                    explanation = explain_methodology(text)
                    _add_message("assistant", f"**🔬 Methodology Explanation:**\n\n{explanation}")

        with col3:
            if st.button("📜 Extract Abstract", use_container_width=True):
                text = st.session_state['chat_full_text']
                abstract = extract_abstract(text)
                _add_message("assistant", f"**📜 Abstract:**\n\n{abstract}")

    # Chat interface
    st.markdown("---")
    st.markdown("### 💬 Chat")

    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []

    # Display chat history
    for message in st.session_state['chat_messages']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    # Chat input
    if prompt := st.chat_input("Ask a question about your paper..."):
        if 'chat_full_text' not in st.session_state:
            with st.chat_message("assistant"):
                st.warning("Please upload a document first before asking questions.")
            return

        # Add user message
        _add_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = _generate_response(prompt)
                st.markdown(response)
                _add_message("assistant", response)

    # Example questions
    if 'chat_full_text' in st.session_state:
        st.markdown("---")
        st.markdown("### 💡 Example Questions")
        examples = [
            "Summarize this paper in 3 sentences",
            "What methodology was used?",
            "What dataset was used in this study?",
            "What are the main findings?",
            "Explain the key contributions",
            "What are the limitations of this study?",
        ]

        cols = st.columns(3)
        for i, example in enumerate(examples):
            with cols[i % 3]:
                if st.button(example, key=f"example_{i}", use_container_width=True):
                    _add_message("user", example)
                    with st.spinner("Generating response..."):
                        response = _generate_response(example)
                        _add_message("assistant", response)
                    st.rerun()

    # Clear chat
    if st.button("🗑️ Clear Chat History"):
        st.session_state['chat_messages'] = []
        st.rerun()


def _add_message(role, content):
    """Add a message to chat history."""
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
    st.session_state['chat_messages'].append({'role': role, 'content': content})


def _generate_response(question):
    """Generate a response to the user's question."""
    # Search vector store for relevant chunks
    vector_store = st.session_state.get('chat_vector_store')
    context_chunks = []

    if vector_store:
        context_chunks = search_vector_store(vector_store, question, top_k=4)

    if not context_chunks:
        # Fallback: use raw chunks with simple keyword matching
        chunks = st.session_state.get('chat_chunks', [])
        question_words = set(question.lower().split())
        scored = []
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            overlap = len(question_words & chunk_words)
            scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        context_chunks = [s[1] for s in scored[:4]]

    # Check for OpenAI API key
    api_key = st.session_state.get('openai_api_key', '')
    if api_key:
        response = answer_question_openai(question, context_chunks, api_key)
        if "error" not in response.lower() and "falling back" not in response.lower():
            return response

    # Use local model
    response = answer_question_local(question, context_chunks)
    return response
