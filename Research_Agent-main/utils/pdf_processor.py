"""
PDF Processor Utility Module

Provides functions to extract text, abstract, references, and metadata from PDF files.
Uses PyMuPDF (fitz), pdfplumber, and PyPDF2 with fallback chain.
"""

import io
import re
import fitz  # PyMuPDF
import pdfplumber
from PyPDF2 import PdfReader


def extract_text_pymupdf(pdf_bytes):
    """Extract text from PDF using PyMuPDF (fitz). Primary method."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")
        return None


def extract_text_pdfplumber(pdf_bytes):
    """Extract text from PDF using pdfplumber. Secondary method."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
        return None


def extract_text_pypdf2(pdf_bytes):
    """Extract text from PDF using PyPDF2. Fallback method."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
        return None


def extract_text_from_pdf(pdf_bytes):
    """
    Extract text from PDF bytes using a fallback chain:
    PyMuPDF → pdfplumber → PyPDF2.
    
    Args:
        pdf_bytes: Raw bytes of the PDF file.
        
    Returns:
        Extracted text string or empty string if all methods fail.
    """
    # Try PyMuPDF first (fastest and most accurate)
    text = extract_text_pymupdf(pdf_bytes)
    if text and len(text) > 50:
        return text

    # Try pdfplumber as secondary
    text = extract_text_pdfplumber(pdf_bytes)
    if text and len(text) > 50:
        return text

    # Try PyPDF2 as final fallback
    text = extract_text_pypdf2(pdf_bytes)
    if text and len(text) > 50:
        return text

    return text or ""


def extract_abstract(text):
    """
    Extract the abstract section from paper text.
    
    Looks for common patterns like 'Abstract', 'ABSTRACT', 'Summary' headings.
    
    Args:
        text: Full text of the paper.
        
    Returns:
        Extracted abstract text or a message if not found.
    """
    # Pattern: "Abstract" followed by content until next section heading
    patterns = [
        r'(?i)\babstract\b[\s:\-]*\n?(.*?)(?=\n\s*(?:1[\.\s]|I[\.\s]|introduction|keywords|key\s*words|index\s*terms))',
        r'(?i)\babstract\b[\s:\-]*\n?(.*?)(?=\n\n\n)',
        r'(?i)\babstract\b[\s:\-]*\n?(.*?)(?=\n\n)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            if len(abstract) > 50:
                return abstract

    # If no pattern matched, try to get the first meaningful paragraph
    paragraphs = text.split('\n\n')
    for para in paragraphs[1:5]:  # Skip title, check first few paragraphs
        para = para.strip()
        if len(para) > 100:
            return para

    return "Abstract not found. The text may not follow a standard paper format."


def extract_references_section(text):
    """
    Extract the References / Bibliography section from paper text.
    
    Args:
        text: Full text of the paper.
        
    Returns:
        Text of the references section.
    """
    # Look for References / Bibliography section
    patterns = [
        r'(?i)\n\s*(?:references|bibliography|works\s+cited|literature\s+cited)\s*\n(.*)',
        r'(?i)\n\s*(?:REFERENCES|BIBLIOGRAPHY)\s*\n(.*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Try to find numbered references at the end
    lines = text.split('\n')
    ref_start = None
    for i in range(len(lines) - 1, max(0, len(lines) - 200), -1):
        line = lines[i].strip()
        if re.match(r'(?i)^\s*(?:references|bibliography)\s*$', line):
            ref_start = i + 1
            break

    if ref_start:
        return '\n'.join(lines[ref_start:]).strip()

    return ""


def extract_metadata(pdf_bytes):
    """
    Extract metadata from PDF (title, author, subject, etc.).
    Includes fallbacks for papers with missing internal metadata.
    
    Args:
        pdf_bytes: Raw bytes of the PDF file.
        
    Returns:
        Dictionary of metadata fields.
    """
    metadata = {
        'title': '',
        'author': '',
        'subject': '',
        'keywords': '',
        'page_count': 0,
    }
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        meta = doc.metadata
        metadata['page_count'] = doc.page_count
        
        if meta:
            metadata['title'] = meta.get('title', '').strip()
            metadata['author'] = meta.get('author', '').strip()
            metadata['subject'] = meta.get('subject', '').strip()
            metadata['keywords'] = meta.get('keywords', '').strip()
            metadata['creator'] = meta.get('creator', '').strip()
            metadata['producer'] = meta.get('producer', '').strip()

        # --- Fallbacks for missing metadata using Font Size Analysis ---
        
        if doc.page_count > 0:
            page = doc[0]
            blocks = page.get_text("dict")["blocks"]
            
            # Extract spans with their font sizes
            spans = []
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            spans.append({
                                "text": s["text"].strip(),
                                "size": s["size"],
                                "font": s["font"],
                                "bbox": s["bbox"]
                            })
            
            if spans:
                # 1. Title Fallback: Find the largest font size
                max_size = max(s["size"] for s in spans if len(s["text"]) > 3)
                
                # Title might be multiple lines with the same (or nearly same) large font
                title_spans = [s for s in spans if s["size"] >= max_size - 1]
                
                # Combine consecutive large spans as the title
                if not metadata['title']:
                    potential_title = " ".join([s["text"] for s in title_spans]).strip()
                    if len(potential_title) > 10:
                        metadata['title'] = potential_title

                # 2. Author Fallback: Find text below title but above abstract
                if not metadata['author'] and metadata['title']:
                    # Get the bottom position of the title
                    title_bottom = max(s["bbox"][3] for s in title_spans)
                    
                    # Find abstract start position
                    abstract_top = 9999
                    for s in spans:
                        if re.search(r'(?i)\babstract\b', s["text"]):
                            abstract_top = s["bbox"][1]
                            break
                    
                    # Authors are usually between title and abstract
                    author_spans = [s for s in spans if s["bbox"][1] > title_bottom and s["bbox"][3] < abstract_top]
                    
                    # Filter out very small text (affiliations) or very large text
                    author_candidates = [s["text"] for s in author_spans if 8 < s["size"] < max_size - 2]
                    
                    if author_candidates:
                        # Take the first line of candidates as primary authors
                        metadata['author'] = author_candidates[0].strip()
                        # If the next candidate looks like more authors, add it
                        if len(author_candidates) > 1 and len(author_candidates[1]) > 3:
                             if not re.search(r'[@\d]', author_candidates[1]): # avoid emails/affiliations
                                 metadata['author'] += ", " + author_candidates[1].strip()

        # 3. Fallback for Keywords (Simple text search)
        if not metadata['keywords'] and doc.page_count > 0:
            first_page_text = doc[0].get_text()
            kw_match = re.search(r'(?i)(?:keywords|index\s*terms|key\s*words)[\s:\-]*\n?(.*?)(?:\n\n|\n\s*(?:I\.|1\.|\bIntroduction\b))', first_page_text, re.DOTALL)
            if kw_match:
                metadata['keywords'] = kw_match.group(1).strip().replace('\n', ' ')

        doc.close()
    except Exception as e:
        print(f"Metadata extraction failed: {e}")

    return metadata


def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into overlapping chunks for embedding and retrieval.
    
    Args:
        text: Input text to chunk.
        chunk_size: Maximum number of words per chunk.
        overlap: Number of overlapping words between chunks.
        
    Returns:
        List of text chunks.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


def get_page_count(pdf_bytes):
    """Get the number of pages in a PDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = doc.page_count
        doc.close()
        return count
    except Exception:
        return 0


def extract_text_by_page(pdf_bytes):
    """
    Extract text page by page from a PDF.
    
    Returns:
        List of (page_number, page_text) tuples.
    """
    pages = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i, page in enumerate(doc):
            text = page.get_text()
            pages.append((i + 1, text.strip()))
        doc.close()
    except Exception as e:
        print(f"Page-by-page extraction failed: {e}")
    return pages
