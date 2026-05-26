"""Text utility functions for papersignals."""

import re
from typing import List


def clean_text(text: str) -> str:
    """Normalize whitespace and strip non-printable characters.

    Args:
        text: Raw input text.

    Returns:
        Cleaned text with normalized whitespace.
    """
    # Strip null bytes and other non-printable chars (except newlines)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize line endings
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse multiple spaces (but keep double newlines for paragraph breaks)
    cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    # Trim leading/trailing whitespace
    cleaned = cleaned.strip()
    return cleaned


def split_sentences(text: str) -> List[str]:
    """Split text into sentences using NLTK with fallback regex.

    Args:
        text: Input text.

    Returns:
        List of sentence strings.
    """
    sentences: List[str] = []
    try:
        import nltk
        # Ensure punkt tokenizer data is available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        sentences = nltk.sent_tokenize(text)
    except (ImportError, LookupError, Exception):
        # Fallback: simple regex-based sentence splitting
        sentences = _regex_split_sentences(text)

    # Filter out empty/whitespace-only sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def _regex_split_sentences(text: str) -> List[str]:
    """Fallback sentence splitting using regex patterns.

    Args:
        text: Input text.

    Returns:
        List of sentence strings.
    """
    # Split on sentence-ending punctuation followed by space and capital letter
    # Handles common abbreviations and decimal numbers
    pattern = r'(?<!\b(?:Mr|Mrs|Ms|Miss|Dr|Prof|Rev|Hon|St|Ave|Blvd|Rd|Dr|Ln|Ct|Pl|Cir|Way|Sq|etc|vs|viz|al|dept|est|govt|approx|appt|apt|dept|est|min|max|no|vol|jr|sr|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Sept|Gen|Sgt|Capt|Lt|Col|Maj|Cpl|Pvt|Sra|Sr|Sres|Srt|Sta|no|vs|etc|e\.g|i\.e|viz|al)\.)(?<!\d\.)(?<=[.!?])\s+(?=[A-Z"\'´`«»""])'
    parts = re.split(pattern, text)
    sentences = []
    for part in parts:
        part = part.strip()
        if part:
            sentences.append(part)
    return sentences if sentences else [text.strip()]


def split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs by double newlines.

    Args:
        text: Input text.

    Returns:
        List of paragraph strings.
    """
    # Normalize line endings first
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Split on two or more consecutive newlines
    paragraphs = re.split(r'\n\s*\n', text)
    # Filter out empty/whitespace-only paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs


def word_count(text: str) -> int:
    """Count the number of words in text.

    Args:
        text: Input text.

    Returns:
        Integer word count.
    """
    if not text or not text.strip():
        return 0
    return len(text.split())
