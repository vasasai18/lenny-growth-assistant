from datetime import date
from pathlib import Path

from app.rag.ingestion import Transcript, chunk_transcript, estimate_tokens


def make_transcript(paragraph_count: int = 60) -> Transcript:
    body = "\n\n".join(
        f"**Guest** (00:{index // 60:02d}:{index % 60:02d}):\n"
        + " ".join(f"word{word}" for word in range(30))
        for index in range(paragraph_count)
    )
    return Transcript(
        title="A test episode",
        guest="Test Guest",
        publication_date=date(2026, 1, 1),
        source_url="https://example.com/episode",
        body=body,
        source_file=Path("test.md"),
    )


def test_chunking_produces_bounded_overlapping_chunks() -> None:
    chunks = chunk_transcript(make_transcript(), target_tokens=650, overlap_tokens=100)

    assert len(chunks) > 1
    assert all(500 <= estimate_tokens(chunk.chunk_text) <= 800 for chunk in chunks[:-1])
    assert all(chunk.timestamp_ref for chunk in chunks)
    assert len({chunk.content_hash for chunk in chunks}) == len(chunks)


def test_chunking_is_deterministic() -> None:
    transcript = make_transcript()
    first = chunk_transcript(transcript)
    second = chunk_transcript(transcript)

    assert [chunk.content_hash for chunk in first] == [
        chunk.content_hash for chunk in second
    ]


def test_overlap_must_be_smaller_than_target() -> None:
    try:
        chunk_transcript(make_transcript(), target_tokens=100, overlap_tokens=100)
    except ValueError as exc:
        assert "overlap" in str(exc).lower()
    else:
        raise AssertionError("Expected invalid overlap configuration to fail")


def test_content_hash_identifies_duplicate_chunks() -> None:
    transcript = make_transcript()
    first = chunk_transcript(transcript)
    duplicate = chunk_transcript(transcript)

    unique = {chunk.content_hash: chunk for chunk in [*first, *duplicate]}

    assert len(unique) == len(first)
