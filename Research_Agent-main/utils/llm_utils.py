"""
LLM Utilities Module

Provides functions for:
- Building FAISS vector stores from document chunks
- Question-answering over documents using local HuggingFace models
- Paper summarization and analysis
- Falls back to extractive summarization when LLM is unavailable
"""

import os
import numpy as np


def get_embeddings_model():
    """
    Load the SentenceTransformer embedding model.
    
    Returns:
        HuggingFaceEmbeddings instance for LangChain compatibility.
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')


def build_vector_store(text_chunks):
    """
    Build a FAISS vector store from text chunks.
    
    Args:
        text_chunks: List of text strings to index.
        
    Returns:
        FAISS vector store instance, or None on failure.
    """
    if not text_chunks:
        return None

    try:
        from langchain_community.vectorstores import FAISS
        from langchain.schema import Document

        embeddings = get_embeddings_model()

        # Create Document objects
        documents = [Document(page_content=chunk) for chunk in text_chunks]

        # Build FAISS index
        vector_store = FAISS.from_documents(documents, embeddings)
        return vector_store

    except Exception as e:
        print(f"Failed to build vector store: {e}")
        return None


def search_vector_store(vector_store, query, top_k=4):
    """
    Search the vector store for relevant chunks.
    
    Args:
        vector_store: FAISS vector store instance.
        query: Query string.
        top_k: Number of results to return.
        
    Returns:
        List of relevant document chunks.
    """
    if vector_store is None:
        return []

    try:
        results = vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]
    except Exception as e:
        print(f"Vector store search failed: {e}")
        return []


def extractive_summarize(text, num_sentences=5):
    """
    Simple extractive summarization by selecting the most important sentences.
    Uses TF-IDF to rank sentence importance.
    
    Args:
        text: Input text to summarize.
        num_sentences: Number of sentences to include in summary.
        
    Returns:
        Summary string.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import nltk
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab', quiet=True)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)

        from nltk.tokenize import sent_tokenize

        sentences = sent_tokenize(text)
        if len(sentences) <= num_sentences:
            return text

        # Use TF-IDF to score sentences
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)

        # Score each sentence by average TF-IDF score
        scores = []
        for i in range(len(sentences)):
            score = float(tfidf_matrix[i].mean())
            scores.append((i, score, sentences[i]))

        # Sort by score and take top sentences
        scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = scores[:num_sentences]

        # Sort by original position to maintain reading order
        top_sentences.sort(key=lambda x: x[0])

        summary = ' '.join([s[2] for s in top_sentences])
        return summary

    except Exception as e:
        print(f"Extractive summarization failed: {e}")
        # Return first N characters as fallback
        return text[:1000] + "..."


def answer_question_local(question, context_chunks, model_pipeline=None):
    """
    Answer a question using retrieved context chunks with a local model.
    
    Uses transformers pipeline for question answering, with fallback to
    extractive approach if model loading fails.
    
    Args:
        question: The user question.
        context_chunks: List of relevant text chunks.
        model_pipeline: Optional pre-loaded pipeline.
        
    Returns:
        Answer string.
    """
    if not context_chunks:
        return "I don't have enough context to answer this question. Please upload a document first."

    context = "\n\n".join(context_chunks)

    # Try using a text2text-generation model
    try:
        if model_pipeline is None:
            from transformers import pipeline
            model_pipeline = pipeline(
                "text2text-generation",
                model="google/flan-t5-small",
                max_new_tokens=256,
            )

        prompt = f"""Based on the following context, answer the question concisely.

Context:
{context[:2000]}

Question: {question}

Answer:"""

        result = model_pipeline(prompt)
        answer = result[0]['generated_text'].strip()

        if answer and len(answer) > 5:
            return answer

    except Exception as e:
        print(f"Local model QA failed: {e}")

    # Fallback: extract most relevant sentence
    return _extractive_answer(question, context_chunks)


def _extractive_answer(question, context_chunks):
    """
    Fallback: find the most relevant sentence to the question using TF-IDF.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import nltk
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab', quiet=True)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        from nltk.tokenize import sent_tokenize

        # Get all sentences from context
        all_sentences = []
        for chunk in context_chunks:
            sents = sent_tokenize(chunk)
            all_sentences.extend(sents)

        if not all_sentences:
            return "Could not find relevant information in the document."

        # Score sentences against question
        texts = [question] + all_sentences
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)

        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        # Get top 3 most relevant sentences
        top_indices = np.argsort(similarities)[-3:][::-1]
        relevant_sentences = [all_sentences[i] for i in top_indices if similarities[i] > 0.05]

        if relevant_sentences:
            return "Based on the document: " + ' '.join(relevant_sentences)
        else:
            return "Could not find relevant information to answer this question. Try rephrasing your question."

    except Exception:
        return "Unable to process the question. Please try again."


def answer_question_openai(question, context_chunks, api_key):
    """
    Answer a question using OpenAI API.
    
    Args:
        question: The user question.
        context_chunks: List of relevant text chunks.
        api_key: OpenAI API key.
        
    Returns:
        Answer string.
    """
    try:
        from langchain_community.llms import OpenAI
        from langchain.chains.question_answering import load_qa_chain
        from langchain.schema import Document

        llm = OpenAI(temperature=0, openai_api_key=api_key)
        chain = load_qa_chain(llm, chain_type="stuff")

        docs = [Document(page_content=chunk) for chunk in context_chunks]
        result = chain.run(input_documents=docs, question=question)
        return result.strip()

    except Exception as e:
        return f"OpenAI API error: {str(e)}. Falling back to local model."


def summarize_paper(text, model_pipeline=None):
    """
    Generate a summary of a research paper.
    
    Args:
        text: Full text of the paper.
        model_pipeline: Optional pre-loaded pipeline.
        
    Returns:
        Summary string.
    """
    # Try using local model first
    try:
        if model_pipeline is None:
            from transformers import pipeline
            model_pipeline = pipeline(
                "text2text-generation",
                model="google/flan-t5-small",
                max_new_tokens=300,
            )

        # Truncate text for model input
        truncated = text[:1500]
        prompt = f"Summarize the following research paper:\n\n{truncated}\n\nSummary:"

        result = model_pipeline(prompt)
        summary = result[0]['generated_text'].strip()

        if summary and len(summary) > 20:
            return summary

    except Exception as e:
        print(f"Model summarization failed: {e}")

    # Fallback to extractive summarization
    return extractive_summarize(text, num_sentences=7)


def explain_methodology(text, model_pipeline=None):
    """
    Extract and explain the methodology section from a paper.
    
    Args:
        text: Full text of the paper.
        model_pipeline: Optional pre-loaded pipeline.
        
    Returns:
        Methodology explanation string.
    """
    import re

    # Try to find methodology section
    patterns = [
        r'(?i)(?:methodology|methods|approach|proposed\s+method)[\s:]*\n(.*?)(?=\n\s*(?:\d+[\.\s]|[IVX]+[\.\s]|results|experiment|evaluation|conclusion))',
        r'(?i)(?:3[\.\s]*methodology|3[\.\s]*methods|III[\.\s]*method)[\s:]*\n(.*?)(?=\n\s*(?:4[\.\s]|IV[\.\s]))',
    ]

    methodology_text = ""
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            methodology_text = match.group(1).strip()
            break

    if not methodology_text:
        # Use middle portion of the paper as approximation
        words = text.split()
        start = len(words) // 4
        end = start + min(500, len(words) // 2)
        methodology_text = ' '.join(words[start:end])

    # Try to generate explanation with model
    try:
        if model_pipeline is None:
            from transformers import pipeline
            model_pipeline = pipeline(
                "text2text-generation",
                model="google/flan-t5-small",
                max_new_tokens=256,
            )

        prompt = f"Explain the methodology described in this text:\n\n{methodology_text[:1500]}\n\nExplanation:"
        result = model_pipeline(prompt)
        explanation = result[0]['generated_text'].strip()

        if explanation and len(explanation) > 20:
            return explanation

    except Exception:
        pass

    # Fallback: return extractive summary of methodology section
    return extractive_summarize(methodology_text, num_sentences=5)
