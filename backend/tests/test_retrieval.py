import uuid
from datetime import date

import pytest

from app.rag.retriever import RetrievedChunk, build_grounded_context, filter_by_relevance


def make_chunk(similarity: float) -> RetrievedChunk:
    return RetrievedChunk(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        episode_title="Product discovery",
        guest_name="Example Guest",
        publication_date=date(2026, 1, 1),
        timestamp_ref="00:10:00–00:12:00",
        source_url="https://example.com/episode",
        chunk_text="Interview customers before committing to a solution.",
        similarity=similarity,
    )


def test_relevance_threshold_includes_boundary() -> None:
    chunks = [make_chunk(0.51), make_chunk(0.52), make_chunk(0.80)]

    assert [chunk.similarity for chunk in filter_by_relevance(chunks, 0.52)] == [
        0.52,
        0.80,
    ]


def test_empty_retrieval_supports_refusal_path() -> None:
    assert filter_by_relevance([make_chunk(0.2)], 0.52) == []


def test_citation_contains_traceable_metadata() -> None:
    citation = make_chunk(0.75).citation(1)

    assert citation["citation_number"] == 1
    assert citation["episode_title"] == "Product discovery"
    assert citation["timestamp_ref"] == "00:10:00–00:12:00"
    assert citation["chunk_id"] == "00000000-0000-0000-0000-000000000001"
    assert citation["similarity"] == 0.75


def test_context_marks_transcript_as_quoted_data() -> None:
    context = build_grounded_context([make_chunk(0.75)])

    assert "<TRANSCRIPT_QUOTE>" in context
    assert "Episode: Product discovery" in context
    assert "Chunk ID:" in context


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_filter_inputs_are_validated_by_retriever(threshold: float) -> None:
    from app.rag.retriever import TranscriptRetriever

    with pytest.raises(ValueError):
        TranscriptRetriever(object(), score_threshold=threshold)  # type: ignore[arg-type]
