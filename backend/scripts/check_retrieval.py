import argparse
import asyncio

from app.config import get_settings
from app.database import AsyncSessionFactory, close_database
from app.rag.embeddings import OllamaEmbeddingClient
from app.rag.retriever import (
    INSUFFICIENT_INFORMATION_MESSAGE,
    TranscriptRetriever,
)


async def run_query(query: str, threshold: float, top_k: int) -> None:
    settings = get_settings()
    embedder = OllamaEmbeddingClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
        expected_dimension=settings.embedding_dimension,
    )
    retriever = TranscriptRetriever(
        embedding_client=embedder,
        score_threshold=threshold,
        default_top_k=top_k,
    )

    async with AsyncSessionFactory() as session:
        chunks = await retriever.search(session, query)

    print(f"Question: {query}")
    print(f"Threshold: {threshold}")
    if not chunks:
        print(INSUFFICIENT_INFORMATION_MESSAGE)
    else:
        for position, chunk in enumerate(chunks, start=1):
            print(
                f"[{position}] similarity={chunk.similarity:.4f} | "
                f"{chunk.episode_title} | {chunk.timestamp_ref}"
            )
            print(f"    {chunk.chunk_text[:180].replace(chr(10), ' ')}...")


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Test semantic transcript retrieval.")
    parser.add_argument("query")
    parser.add_argument(
        "--threshold", type=float, default=settings.retrieval_score_threshold
    )
    parser.add_argument("--top-k", type=int, default=settings.retrieval_top_k)
    args = parser.parse_args()

    async def run() -> None:
        try:
            await run_query(args.query, args.threshold, args.top_k)
        finally:
            await close_database()

    asyncio.run(run())


if __name__ == "__main__":
    main()

