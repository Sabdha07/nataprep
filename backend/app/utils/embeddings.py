"""
Embedding utilities — Phase 2.
Generates and stores vector embeddings via Qdrant for semantic search and dedup.
"""
from app.core.config import settings
import structlog

log = structlog.get_logger()


async def get_text_embedding(text: str) -> list[float] | None:
    """
    Generate a text embedding. In Phase 1, returns None (embeddings disabled).
    In Phase 2, this calls the embedding API and returns a vector.
    """
    if not settings.OPENAI_API_KEY:
        return None
    # TODO Phase 2: Call embedding API here
    # For now return None to skip vector operations gracefully
    return None


async def store_question_embedding(question_id: str, embedding: list[float]) -> str | None:
    """Store embedding in Qdrant. Returns the point ID."""
    if embedding is None:
        return None
    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import PointStruct
        client = AsyncQdrantClient(url=settings.QDRANT_URL)
        point = PointStruct(id=question_id, vector=embedding, payload={"question_id": question_id})
        await client.upsert(
            collection_name=settings.QDRANT_COLLECTION_QUESTIONS,
            points=[point],
        )
        return question_id
    except Exception as e:
        log.warning("qdrant_store_failed", error=str(e))
        return None


async def semantic_similarity_search(
    query_embedding: list[float],
    collection: str,
    top_k: int = 5,
    score_threshold: float = 0.85,
) -> list[dict]:
    """Search for semantically similar items in Qdrant."""
    if query_embedding is None:
        return []
    try:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(url=settings.QDRANT_URL)
        results = await client.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
        )
        return [{"id": str(r.id), "score": r.score, "payload": r.payload} for r in results]
    except Exception as e:
        log.warning("qdrant_search_failed", error=str(e))
        return []
