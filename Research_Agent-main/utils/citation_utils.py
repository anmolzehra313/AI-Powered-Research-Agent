"""
Citation Utilities Module

Provides functions to parse reference strings into structured data,
generate BibTeX entries, and export citations.
"""

import re
import pandas as pd
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


def parse_reference_string(ref_string):
    """
    Parse a single reference string into structured components.
    
    Attempts to extract: authors, title, journal/conference, year, DOI, volume, pages.
    
    Args:
        ref_string: Raw reference text string.
        
    Returns:
        Dictionary with parsed fields.
    """
    result = {
        'raw': ref_string.strip(),
        'authors': '',
        'title': '',
        'journal': '',
        'year': '',
        'doi': '',
        'volume': '',
        'pages': '',
    }

    text = ref_string.strip()

    # Remove leading reference number like [1], [2], 1., 2., etc.
    text = re.sub(r'^\s*\[?\d+\]?[\.\)\s]*', '', text)

    # 1. Extract Year (4-digit number between 1900-2099)
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        result['year'] = year_match.group(0)

    # 2. Extract DOI
    doi_match = re.search(r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)(10\.\d{4,}/[^\s,;]+)', text, re.IGNORECASE)
    if doi_match:
        result['doi'] = doi_match.group(1).rstrip('.')

    # 3. Extract Pages
    pages_match = re.search(r'pp?\.\s*(\d+[\s]*[-–]\s*\d+)', text)
    if pages_match:
        result['pages'] = pages_match.group(1)

    # 4. Extract Volume
    vol_match = re.search(r'[Vv]ol\.?\s*(\d+)', text)
    if vol_match:
        result['volume'] = vol_match.group(1)

    # 5. Extract Title (Look for text in quotes first)
    quoted_title_match = re.search(r'["“]([^"”]{10,})["”]', text)
    if quoted_title_match:
        result['title'] = quoted_title_match.group(1).strip()
        # Authors are usually before the title
        authors_part = text[:quoted_title_match.start()].strip().rstrip(',').rstrip('.')
        result['authors'] = authors_part
        # Journal is usually after the title
        journal_part = text[quoted_title_match.end():].strip().lstrip(',').lstrip('.')
        # Clean journal part (remove year, pages, volume if already found)
        journal_part = re.sub(r'\b(19|20)\d{2}\b', '', journal_part)
        journal_part = re.sub(r'pp?\.\s*\d+[-–]\d+', '', journal_part)
        journal_part = re.sub(r'[Vv]ol\.?\s*\d+', '', journal_part)
        result['journal'] = journal_part.split(',')[0].strip().rstrip('.')
    else:
        # Fallback for citations without quotes
        # Pattern: Authors. Title. Journal...
        # We need to split by periods but ignore periods in initials (e.g., "K. Shafiq")
        # Regex for dot NOT preceded by a single capital letter
        parts = re.split(r'(?<!\b[A-Z])\.\s+', text)
        
        if len(parts) >= 3:
            result['authors'] = parts[0].strip()
            result['title'] = parts[1].strip()
            result['journal'] = parts[2].strip().split(',')[0].strip()
        elif len(parts) == 2:
            # Maybe Authors, "Title" or Authors. Title
            if ',' in parts[0] and len(parts[0]) > 10:
                result['authors'] = parts[0].strip()
                result['title'] = parts[1].strip()
            else:
                result['title'] = parts[0].strip()
                result['journal'] = parts[1].strip()

    # Clean up extracted fields
    for key in result:
        if isinstance(result[key], str):
            result[key] = result[key].strip()
            # Remove any trailing commas or periods from main fields
            if key in ['authors', 'title', 'journal']:
                result[key] = result[key].rstrip(',').rstrip('.')
            # Remove quotes around values
            result[key] = result[key].strip('"').strip('“').strip('”')

    return result


def parse_references_from_text(references_text):
    """
    Parse a block of reference text into a list of structured citations.
    
    Args:
        references_text: Text containing multiple references.
        
    Returns:
        List of dictionaries with parsed citation data.
    """
    if not references_text:
        return []

    # Split references by numbered patterns or blank lines
    # Pattern: [1], [2], ... or 1., 2., ... or 1), 2), ...
    ref_pattern = re.split(r'\n\s*(?=\[\d+\]|\d+[\.\)])', references_text)

    citations = []
    for ref in ref_pattern:
        ref = ref.strip()
        if len(ref) > 20:  # Minimum length for a valid reference
            parsed = parse_reference_string(ref)
            citations.append(parsed)

    # If splitting didn't work well, try splitting by double newlines
    if len(citations) <= 1:
        refs_by_line = references_text.split('\n\n')
        citations = []
        for ref in refs_by_line:
            ref = ref.strip()
            if len(ref) > 20:
                parsed = parse_reference_string(ref)
                citations.append(parsed)

    # Last resort: split by single newlines for long lines
    if len(citations) <= 1:
        refs_by_line = references_text.split('\n')
        citations = []
        for ref in refs_by_line:
            ref = ref.strip()
            if len(ref) > 30:
                parsed = parse_reference_string(ref)
                citations.append(parsed)

    return citations


def generate_bibtex_entry(citation, entry_id=None):
    """
    Generate a BibTeX entry string from a parsed citation dictionary.
    
    Args:
        citation: Dictionary with keys: authors, title, journal, year, doi, volume, pages.
        entry_id: Optional custom entry ID.
        
    Returns:
        BibTeX entry string.
    """
    if not entry_id:
        # Generate ID from first author's last name and year
        author_part = citation.get('authors', 'unknown').split(',')[0].split()[-1] if citation.get('authors') else 'unknown'
        year_part = citation.get('year', 'XXXX')
        entry_id = f"{author_part.lower()}{year_part}"
        # Remove special characters from ID
        entry_id = re.sub(r'[^a-zA-Z0-9]', '', entry_id)

    entry_type = 'article' if citation.get('journal') else 'misc'

    bibtex = f"@{entry_type}{{{entry_id},\n"
    if citation.get('authors'):
        bibtex += f"  author = {{{citation['authors']}}},\n"
    if citation.get('title'):
        bibtex += f"  title = {{{citation['title']}}},\n"
    if citation.get('journal'):
        bibtex += f"  journal = {{{citation['journal']}}},\n"
    if citation.get('year'):
        bibtex += f"  year = {{{citation['year']}}},\n"
    if citation.get('volume'):
        bibtex += f"  volume = {{{citation['volume']}}},\n"
    if citation.get('pages'):
        bibtex += f"  pages = {{{citation['pages']}}},\n"
    if citation.get('doi'):
        bibtex += f"  doi = {{{citation['doi']}}},\n"
    bibtex += "}\n"

    return bibtex


def generate_bibtex_from_citations(citations):
    """
    Generate complete BibTeX string from a list of parsed citations.
    
    Args:
        citations: List of citation dictionaries.
        
    Returns:
        Complete BibTeX string with all entries.
    """
    bibtex_entries = []
    used_ids = set()

    for i, citation in enumerate(citations):
        author_part = citation.get('authors', 'unknown').split(',')[0].split()[-1] if citation.get('authors') else 'unknown'
        year_part = citation.get('year', 'XXXX')
        base_id = re.sub(r'[^a-zA-Z0-9]', '', f"{author_part.lower()}{year_part}")

        entry_id = base_id
        counter = 1
        while entry_id in used_ids:
            entry_id = f"{base_id}{chr(96 + counter)}"  # a, b, c, ...
            counter += 1
        used_ids.add(entry_id)

        bibtex_entries.append(generate_bibtex_entry(citation, entry_id))

    return '\n'.join(bibtex_entries)


def citations_to_dataframe(citations):
    """
    Convert a list of citation dictionaries to a pandas DataFrame.
    
    Args:
        citations: List of citation dictionaries.
        
    Returns:
        pandas DataFrame with citation data.
    """
    if not citations:
        return pd.DataFrame()

    df = pd.DataFrame(citations)
    # Reorder columns for display
    display_cols = ['authors', 'title', 'journal', 'year', 'volume', 'pages', 'doi', 'raw']
    existing_cols = [c for c in display_cols if c in df.columns]
    return df[existing_cols]


def citations_to_csv(citations):
    """
    Convert citations to CSV bytes with UTF-8-SIG encoding.
    UTF-8-SIG (with BOM) ensures that Excel opens the file with correct character encoding.
    """
    df = citations_to_dataframe(citations)
    csv_str = df.to_csv(index=False)
    return csv_str.encode('utf-8-sig')


def parse_bibtex_string(bibtex_string):
    """
    Parse a BibTeX string into a list of citation dictionaries.
    
    Args:
        bibtex_string: BibTeX formatted string.
        
    Returns:
        List of citation dictionaries.
    """
    try:
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_database = bibtexparser.loads(bibtex_string, parser=parser)

        citations = []
        for entry in bib_database.entries:
            citation = {
                'authors': entry.get('author', ''),
                'title': entry.get('title', ''),
                'journal': entry.get('journal', entry.get('booktitle', '')),
                'year': entry.get('year', ''),
                'volume': entry.get('volume', ''),
                'pages': entry.get('pages', ''),
                'doi': entry.get('doi', ''),
                'raw': '',
            }
            citations.append(citation)

        return citations
    except Exception as e:
        print(f"BibTeX parsing failed: {e}")
        return []
