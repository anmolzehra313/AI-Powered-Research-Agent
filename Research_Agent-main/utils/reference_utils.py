"""
Reference Formatting Utilities Module

Provides functions to format citations in APA, IEEE, MLA, and Harvard styles.
Also generates BibTeX entries and supports batch formatting.
"""


def format_apa(reference):
    """
    Format a reference in APA style (7th Edition).
    
    Format: Author(s) (Year). Title. Journal, Volume(Issue), Pages. DOI
    
    Args:
        reference: Dictionary with keys: authors, year, title, journal, volume, issue, pages, doi
        
    Returns:
        Formatted APA string.
    """
    parts = []

    # Authors
    authors = reference.get('authors', '').strip()
    if authors:
        # Convert "First Last" to "Last, F."
        author_list = [a.strip() for a in authors.split(',') if a.strip()]
        formatted_authors = []
        for author in author_list:
            names = author.strip().split()
            if len(names) >= 2:
                last = names[-1]
                initials = '. '.join([n[0].upper() for n in names[:-1]])
                formatted_authors.append(f"{last}, {initials}.")
            elif names:
                formatted_authors.append(names[0])

        if len(formatted_authors) > 1:
            parts.append(', '.join(formatted_authors[:-1]) + ', & ' + formatted_authors[-1])
        elif formatted_authors:
            parts.append(formatted_authors[0])

    # Year
    year = reference.get('year', '').strip()
    if year:
        parts.append(f"({year})")

    # Title
    title = reference.get('title', '').strip()
    if title:
        # APA: capitalize only first word and proper nouns
        parts.append(f"{title}.")

    # Journal (italicized in text representation)
    journal = reference.get('journal', '').strip()
    if journal:
        journal_part = journal
        volume = reference.get('volume', '').strip()
        issue = reference.get('issue', '').strip()
        pages = reference.get('pages', '').strip()

        if volume:
            journal_part += f", {volume}"
            if issue:
                journal_part += f"({issue})"
        if pages:
            journal_part += f", {pages}"
        parts.append(f"{journal_part}.")

    # DOI
    doi = reference.get('doi', '').strip()
    if doi:
        if not doi.startswith('http'):
            doi = f"https://doi.org/{doi}"
        parts.append(doi)

    return ' '.join(parts)


def format_ieee(reference):
    """
    Format a reference in IEEE style.
    
    Format: [#] A. Author, "Title," Journal, vol. V, no. N, pp. P1-P2, Year.
    
    Args:
        reference: Dictionary with reference fields.
        
    Returns:
        Formatted IEEE string.
    """
    parts = []

    # Authors - IEEE uses initials first
    authors = reference.get('authors', '').strip()
    if authors:
        author_list = [a.strip() for a in authors.split(',') if a.strip()]
        formatted_authors = []
        for author in author_list:
            names = author.strip().split()
            if len(names) >= 2:
                initials = '. '.join([n[0].upper() for n in names[:-1]])
                last = names[-1]
                formatted_authors.append(f"{initials}. {last}")
            elif names:
                formatted_authors.append(names[0])

        if len(formatted_authors) > 1:
            parts.append(', '.join(formatted_authors[:-1]) + ' and ' + formatted_authors[-1])
        elif formatted_authors:
            parts.append(formatted_authors[0])

    # Title in quotes
    title = reference.get('title', '').strip()
    if title:
        parts.append(f'"{title},"')

    # Journal (italicized)
    journal = reference.get('journal', '').strip()
    if journal:
        parts.append(f"{journal},")

    # Volume
    volume = reference.get('volume', '').strip()
    if volume:
        parts.append(f"vol. {volume},")

    # Issue
    issue = reference.get('issue', '').strip()
    if issue:
        parts.append(f"no. {issue},")

    # Pages
    pages = reference.get('pages', '').strip()
    if pages:
        parts.append(f"pp. {pages},")

    # Year
    year = reference.get('year', '').strip()
    if year:
        parts.append(f"{year}.")

    # DOI
    doi = reference.get('doi', '').strip()
    if doi:
        if not doi.startswith('http'):
            doi = f"doi: {doi}"
        parts.append(doi)

    return ' '.join(parts)


def format_mla(reference):
    """
    Format a reference in MLA style (9th Edition).
    
    Format: Author(s). "Title." Journal, vol. V, no. N, Year, pp. Pages.
    
    Args:
        reference: Dictionary with reference fields.
        
    Returns:
        Formatted MLA string.
    """
    parts = []

    # Authors - MLA uses "Last, First" for first author
    authors = reference.get('authors', '').strip()
    if authors:
        author_list = [a.strip() for a in authors.split(',') if a.strip()]
        formatted_authors = []
        for i, author in enumerate(author_list):
            names = author.strip().split()
            if len(names) >= 2:
                if i == 0:
                    # First author: Last, First
                    formatted_authors.append(f"{names[-1]}, {' '.join(names[:-1])}")
                else:
                    # Subsequent: First Last
                    formatted_authors.append(' '.join(names))
            elif names:
                formatted_authors.append(names[0])

        if len(formatted_authors) > 2:
            parts.append(f"{formatted_authors[0]}, et al.")
        elif len(formatted_authors) == 2:
            parts.append(f"{formatted_authors[0]}, and {formatted_authors[1]}.")
        elif formatted_authors:
            parts.append(f"{formatted_authors[0]}.")

    # Title in quotes
    title = reference.get('title', '').strip()
    if title:
        parts.append(f'"{title}."')

    # Journal (italicized)
    journal = reference.get('journal', '').strip()
    if journal:
        journal_part = journal

        volume = reference.get('volume', '').strip()
        if volume:
            journal_part += f", vol. {volume}"

        issue = reference.get('issue', '').strip()
        if issue:
            journal_part += f", no. {issue}"

        year = reference.get('year', '').strip()
        if year:
            journal_part += f", {year}"

        pages = reference.get('pages', '').strip()
        if pages:
            journal_part += f", pp. {pages}"

        parts.append(f"{journal_part}.")
    else:
        year = reference.get('year', '').strip()
        if year:
            parts.append(f"{year}.")

    # DOI
    doi = reference.get('doi', '').strip()
    if doi:
        if not doi.startswith('http'):
            doi = f"https://doi.org/{doi}"
        parts.append(doi)

    return ' '.join(parts)


def format_harvard(reference):
    """
    Format a reference in Harvard style.
    
    Format: Author(s) (Year) Title. Journal, Volume(Issue), pp. Pages.
    
    Args:
        reference: Dictionary with reference fields.
        
    Returns:
        Formatted Harvard string.
    """
    parts = []

    # Authors
    authors = reference.get('authors', '').strip()
    if authors:
        author_list = [a.strip() for a in authors.split(',') if a.strip()]
        formatted_authors = []
        for author in author_list:
            names = author.strip().split()
            if len(names) >= 2:
                last = names[-1]
                initials = '.'.join([n[0].upper() for n in names[:-1]])
                formatted_authors.append(f"{last}, {initials}.")
            elif names:
                formatted_authors.append(names[0])

        if len(formatted_authors) > 3:
            parts.append(f"{formatted_authors[0]} et al.")
        elif len(formatted_authors) > 1:
            parts.append(', '.join(formatted_authors[:-1]) + ' and ' + formatted_authors[-1])
        elif formatted_authors:
            parts.append(formatted_authors[0])

    # Year
    year = reference.get('year', '').strip()
    if year:
        parts.append(f"({year})")

    # Title
    title = reference.get('title', '').strip()
    if title:
        parts.append(f"{title}.")

    # Journal with volume and pages
    journal = reference.get('journal', '').strip()
    if journal:
        journal_part = journal
        volume = reference.get('volume', '').strip()
        issue = reference.get('issue', '').strip()
        pages = reference.get('pages', '').strip()

        if volume:
            journal_part += f", {volume}"
            if issue:
                journal_part += f"({issue})"
        if pages:
            journal_part += f", pp. {pages}"
        parts.append(f"{journal_part}.")

    # DOI
    doi = reference.get('doi', '').strip()
    if doi:
        if not doi.startswith('http'):
            doi = f"https://doi.org/{doi}"
        parts.append(f"Available at: {doi}")

    return ' '.join(parts)


def format_reference(reference, style='apa'):
    """
    Format a reference in the specified style.
    
    Args:
        reference: Dictionary with reference fields.
        style: One of 'apa', 'ieee', 'mla', 'harvard'.
        
    Returns:
        Formatted reference string.
    """
    formatters = {
        'apa': format_apa,
        'ieee': format_ieee,
        'mla': format_mla,
        'harvard': format_harvard,
    }

    formatter = formatters.get(style.lower(), format_apa)
    return formatter(reference)


def format_references_batch(references, style='apa'):
    """
    Format a list of references in the specified style.
    
    Args:
        references: List of reference dictionaries.
        style: One of 'apa', 'ieee', 'mla', 'harvard'.
        
    Returns:
        List of formatted reference strings.
    """
    formatted = []
    for i, ref in enumerate(references, 1):
        formatted_ref = format_reference(ref, style)
        if style.lower() == 'ieee':
            formatted.append(f"[{i}] {formatted_ref}")
        else:
            formatted.append(formatted_ref)
    return formatted


def generate_bibtex(reference, entry_id=None):
    """
    Generate a BibTeX entry from a reference dictionary.
    
    Args:
        reference: Dictionary with reference fields.
        entry_id: Custom entry ID (optional).
        
    Returns:
        BibTeX entry string.
    """
    import re

    if not entry_id:
        authors = reference.get('authors', 'unknown')
        first_author = authors.split(',')[0].split()[-1] if authors else 'unknown'
        year = reference.get('year', 'XXXX')
        entry_id = re.sub(r'[^a-zA-Z0-9]', '', f"{first_author.lower()}{year}")

    entry_type = 'article' if reference.get('journal') else 'misc'

    lines = [f"@{entry_type}{{{entry_id},"]

    field_map = {
        'authors': 'author',
        'title': 'title',
        'journal': 'journal',
        'year': 'year',
        'volume': 'volume',
        'issue': 'number',
        'pages': 'pages',
        'doi': 'doi',
    }

    for src_key, bib_key in field_map.items():
        value = reference.get(src_key, '').strip()
        if value:
            lines.append(f"  {bib_key} = {{{value}}},")

    lines.append("}")
    return '\n'.join(lines)


def generate_bibtex_batch(references):
    """Generate BibTeX entries for a list of references."""
    entries = []
    used_ids = set()

    for ref in references:
        authors = ref.get('authors', 'unknown')
        first_author = authors.split(',')[0].split()[-1] if authors else 'unknown'
        year = ref.get('year', 'XXXX')

        import re
        base_id = re.sub(r'[^a-zA-Z0-9]', '', f"{first_author.lower()}{year}")
        entry_id = base_id
        counter = 1
        while entry_id in used_ids:
            entry_id = f"{base_id}{chr(96 + counter)}"
            counter += 1
        used_ids.add(entry_id)

        entries.append(generate_bibtex(ref, entry_id))

    return '\n\n'.join(entries)
