"""Document parsing for papersignals."""

import os
from typing import Dict, List, Optional

from papersignals.utils.text_utils import (
    clean_text,
    split_sentences,
    split_paragraphs,
    word_count,
)


def parse_document(path: str) -> Dict:
    """Read a file and extract its text content.

    Supports .txt, .md, and .docx files.

    Args:
        path: Path to the document file.

    Returns:
        Dict with keys: 'text' (str), 'path' (str), 'name' (str).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    name = os.path.basename(path)

    if ext in (".txt", ".md"):
        text = _read_text_file(path)
    elif ext == ".docx":
        text = _read_docx_file(path)
    else:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported formats: .txt, .md, .docx"
        )

    return {
        "text": text,
        "path": os.path.abspath(path),
        "name": name,
    }


def _read_text_file(path: str) -> str:
    """Read a plain text or markdown file.

    Args:
        path: Path to the file.

    Returns:
        File contents as a string.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _read_docx_file(path: str) -> str:
    """Read a .docx file and extract its text.

    Uses python-docx if available; otherwise falls back to basic
    zip-based extraction.

    Args:
        path: Path to the .docx file.

    Returns:
        Extracted text content.
    """
    try:
        import docx
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        return _read_docx_fallback(path)


def _read_docx_fallback(path: str) -> str:
    """Fallback .docx reader using zipfile and XML parsing.

    Args:
        path: Path to the .docx file.

    Returns:
        Extracted text content.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    text_parts: List[str] = []
    with zipfile.ZipFile(path) as z:
        # Find the document.xml file inside the archive
        if "word/document.xml" in z.namelist():
            xml_content = z.read("word/document.xml")
            root = ET.fromstring(xml_content)
            # Namespace for the main document
            ns = {
                "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            }
            for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                texts = []
                for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                    if t.text:
                        texts.append(t.text)
                if texts:
                    text_parts.append("".join(texts))
    return "\n\n".join(text_parts)


def segment_text(text: str) -> Dict:
    """Split text into sentences and paragraphs with metadata.

    Args:
        text: Input text to segment.

    Returns:
        Dict with keys:
            'sentences' (List[str]),
            'paragraphs' (List[str]),
            'word_count' (int),
            'sentence_count' (int),
            'paragraph_count' (int).
    """
    cleaned = clean_text(text)

    sentences = split_sentences(cleaned)
    paragraphs = split_paragraphs(cleaned)

    # If paragraph splitting yielded nothing useful, treat whole text as one paragraph
    if not paragraphs and cleaned.strip():
        paragraphs = [cleaned.strip()]

    return {
        "sentences": sentences,
        "paragraphs": paragraphs,
        "word_count": word_count(cleaned),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
    }
