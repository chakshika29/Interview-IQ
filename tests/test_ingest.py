import tempfile
import os
from app.ingest import (
    load_document,
    split_sentences,
    split_text,
    split_text_by_boundaries,
)


def test_split_sentences():
    """Verify sentence splitter isolates sentences based on punctuation."""
    text = "LangGraph is a stateful framework. It enables cyclic graphs! Does it support checkpointers? Yes."
    sentences = split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "LangGraph is a stateful framework."
    assert sentences[1] == "It enables cyclic graphs!"
    assert sentences[2] == "Does it support checkpointers?"
    assert sentences[3] == "Yes."


def test_split_text_by_boundaries():
    """Verify boundary chunking groups complete sentences without mid-word splits."""
    text = (
        "First complete sentence here. Second complete sentence here. "
        "Third complete sentence here.\n\n"
        "Second paragraph starts here. It has more details."
    )
    chunks = split_text_by_boundaries(text, target_size=100, overlap=0)
    assert len(chunks) >= 2
    # Ensure no chunk ends with a sliced word
    for c in chunks:
        assert not c.endswith(" ")
        assert len(c) > 0


def test_legacy_split_text():
    """Verify legacy fixed-character chunker produces expected piece counts."""
    text = "A" * 1500
    pieces = split_text(text, size=500, overlap=100)
    # 0:500, 400:900, 800:1300, 1200:1500 -> 4 pieces
    assert len(pieces) == 4


def test_load_document_text_file():
    """Verify load_document loads, chunks, and tags a raw text document."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write("Line one of job description.\n\nLine two has more requirements for Python engineers.")
        temp_path = f.name

    try:
        chunks = load_document(temp_path, source="job_description", chunk_size=500)
        assert len(chunks) >= 1
        assert chunks[0].source == "job_description"
        assert chunks[0].page == 1
        assert chunks[0].id.startswith("job_description-1-")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
