import os
import re
from typing import Any
from pypdf import PdfReader
from app.schemas import Chunk


def read_pages(path: str) -> list[tuple[int, str]]:
    """
    Return a list of (page_number, text) tuples from PDF, DOCX, or text file.
    """
    lower = path.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(path)
        pages = []
        for i, p in enumerate(reader.pages):
            text = p.extract_text() or ""
            pages.append((i + 1, text))
        return pages

    if lower.endswith(".docx"):
        import docx
        doc = docx.Document(path)
        lines = []
        for p in doc.paragraphs:
            if p.text.strip():
                lines.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if row_cells:
                    lines.append(" | ".join(dict.fromkeys(row_cells)))
        full_text = "\n\n".join(lines)
        return [(1, full_text)]

    # Standard plain text file
    with open(path, encoding="utf-8", errors="replace") as f:
        return [(1, f.read())]


def validate_document_content(text: str, filename: str = "document", min_words: int = 15) -> str:
    """
    Validate that extracted document text is non-empty, readable, and meets minimum content length.
    """
    clean = text.strip()
    if not clean:
        raise ValueError(f"Uploaded file '{filename}' contains no readable text or is an empty/scanned document.")

    words = clean.split()
    if len(words) < min_words:
        raise ValueError(
            f"Uploaded file '{filename}' has insufficient content ({len(words)} words). "
            f"Please provide a complete document with at least {min_words} words."
        )
    return clean


def split_sentences(text: str) -> list[str]:
    """
    Split text into individual sentences while preserving punctuation and meaning.
    """
    clean = text.replace("\r", " ").replace("\xa0", " ")
    raw_sentences = re.split(r"(?<=[.!?])\s+", clean)
    return [s.strip() for s in raw_sentences if s.strip()]


def split_text_by_boundaries(text: str, target_size: int = 600, overlap: int = 100) -> list[str]:
    """
    Chunk text along natural paragraph and sentence boundaries.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks = []
    current_units = []
    current_length = 0

    units = []
    for para in paragraphs:
        if len(para) <= target_size:
            units.append(para)
        else:
            sentences = split_sentences(para)
            units.extend(sentences if sentences else [para])

    for unit in units:
        unit_len = len(unit)

        if current_length + unit_len > target_size and current_units:
            chunk_content = " ".join(current_units)
            chunks.append(chunk_content)

            if overlap > 0 and len(current_units[-1]) < target_size:
                current_units = [current_units[-1]]
                current_length = len(current_units[0])
            else:
                current_units = []
                current_length = 0

        current_units.append(unit)
        current_length += unit_len + 1

    if current_units:
        chunks.append(" ".join(current_units))

    return chunks


def split_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Legacy fixed-character chunking (retained for backward compatibility and benchmarking)."""
    pieces, start = [], 0
    while start < len(text):
        pieces.append(text[start : start + size])
        start += size - overlap
    return pieces


def load_document(
    path: str,
    source: str,
    chunk_size: int = 600,
    overlap: int = 100,
    use_boundaries: bool = True,
    session_id: str | None = None,
) -> list[Chunk]:
    """
    Load a document and split it into typed Chunk objects.
    """
    chunks = []
    pages = read_pages(path)
    prefix = f"{session_id}-{source}" if session_id else source

    for page, text in pages:
        clean_text = text.strip()
        if not clean_text:
            continue

        if use_boundaries:
            pieces = split_text_by_boundaries(clean_text, target_size=chunk_size, overlap=overlap)
        else:
            pieces = split_text(clean_text, size=chunk_size, overlap=overlap)

        for j, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    id=f"{prefix}-{page}-{j}",
                    text=piece,
                    source=source,
                    page=page,
                )
            )
    return chunks


def extract_document_preview(text: str) -> dict[str, Any]:
    """
    Extract a quick summary preview of the document: word count, detected sections, and snippet.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    word_count = len(text.split())
    char_count = len(text)

    # Heuristic section headers detection
    potential_sections = []
    common_headers = [
        "education", "experience", "projects", "skills", "technical skills",
        "work experience", "certifications", "summary", "responsibilities",
        "requirements", "qualifications", "preferred qualifications",
    ]
    for line in lines:
        cleaned_line = line.lower().rstrip(":")
        if cleaned_line in common_headers or (len(line) < 40 and line.isupper() and len(line) > 3):
            if line not in potential_sections:
                potential_sections.append(line)

    return {
        "word_count": word_count,
        "char_count": char_count,
        "line_count": len(lines),
        "detected_sections": potential_sections[:8],
        "preview_snippet": text[:500] + ("..." if len(text) > 500 else ""),
    }
