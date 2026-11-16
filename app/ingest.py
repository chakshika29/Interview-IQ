import re
from pypdf import PdfReader
from app.schemas import Chunk


def read_pages(path: str) -> list[tuple[int, str]]:
    """
    Return a list of (page_number, text) tuples from a PDF or text file.

    WHY: Different file types require different extractors: pypdf extracts text
    per page from PDFs, while standard UTF-8 text files have a single page.
    """
    if path.lower().endswith(".pdf"):
        pages = PdfReader(path).pages
        return [(i + 1, p.extract_text() or "") for i, p in enumerate(pages)]
    with open(path, encoding="utf-8") as f:
        return [(1, f.read())]


def split_sentences(text: str) -> list[str]:
    """
    Split text into individual sentences while preserving punctuation and meaning.

    WHY: Breaking sentences mid-stream ruins semantic context for vector search.
    Using regex looking for sentence terminators (. ! ?) keeps ideas intact.
    """
    # Normalize carriage returns and non-breaking spaces
    clean = text.replace("\r", " ").replace("\xa0", " ")
    # Match sentences ending with punctuation followed by whitespace
    raw_sentences = re.split(r"(?<=[.!?])\s+", clean)
    return [s.strip() for s in raw_sentences if s.strip()]


def split_text_by_boundaries(text: str, target_size: int = 600, overlap: int = 100) -> list[str]:
    """
    Chunk text along natural paragraph and sentence boundaries.

    WHY: Fixed character splitting (e.g. text[start:start+size]) cuts words and sentences
    in half. Paragraph and sentence boundary chunking ensures that each chunk represents
    a complete, coherent thought for more accurate embedding retrieval.
    """
    # Step 1: Split into paragraphs by blank lines or bullet lists
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        # Fallback if there are no blank lines: treat whole text as one paragraph
        paragraphs = [text.strip()] if text.strip() else []

    chunks = []
    current_units = []
    current_length = 0

    # Expand paragraphs into sentences if a single paragraph exceeds target_size
    units = []
    for para in paragraphs:
        if len(para) <= target_size:
            units.append(para)
        else:
            sentences = split_sentences(para)
            units.extend(sentences if sentences else [para])

    for unit in units:
        unit_len = len(unit)

        # If adding this unit exceeds target_size, flush the accumulated chunk
        if current_length + unit_len > target_size and current_units:
            chunk_content = " ".join(current_units)
            chunks.append(chunk_content)

            # Carry over the last unit for overlap if it is reasonably sized
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
    """
    Legacy fixed-character chunking (retained for backward compatibility and benchmarking).

    WHY: Keeping the original chunker allows us to benchmark naive fixed chunking
    against sentence-boundary chunking in Phase 4 evaluations.
    """
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
) -> list[Chunk]:
    """
    Load a document and split it into typed Chunk objects.

    WHY: Encapsulating the extraction into Chunk objects tags every piece with its
    document source ('resume' or 'job_description') and original page number for citations.
    """
    chunks = []
    for page, text in read_pages(path):
        if use_boundaries:
            pieces = split_text_by_boundaries(text, target_size=chunk_size, overlap=overlap)
        else:
            pieces = split_text(text, size=chunk_size, overlap=overlap)

        for j, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    id=f"{source}-{page}-{j}",
                    text=piece,
                    source=source,
                    page=page,
                )
            )
    return chunks
