from __future__ import annotations

from functools import lru_cache

from pgvector.psycopg2 import register_vector
from psycopg2.pool import SimpleConnectionPool

from src.config.app_config import get_app_config
from src.config.settings import get_settings
from src.embeddings.embedding_service import get_embeddings
import numpy as np


def _distance_to_confidence(distance: float) -> float:
    return 1 - (distance / 2)


@lru_cache
def _get_connection_pool() -> SimpleConnectionPool:

    settings = get_settings()
    pool = SimpleConnectionPool(
        1,
        5,
        settings.database_url,
    )

    return pool


def _get_connection():

    pool = _get_connection_pool()
    connection = pool.getconn()
    register_vector(connection)
    return pool, connection


def _release_connection(pool, connection) -> None:

    pool.putconn(connection)


def search_chunks(
    query: str,
    top_k: int | None = None,
    doc_type: str | None = None,
) -> list[dict]:

    config = get_app_config()
    embeddings = get_embeddings()
    query_vector = np.array(embeddings.embed_query(query))
    limit = top_k if top_k is not None else config.retrieval.top_k

    pool, connection = _get_connection()

    try:
        with connection.cursor() as cursor:
            if doc_type is None:
                cursor.execute(
                    """
                    SELECT id, chunk_text, metadata, embedding <=> %s AS distance
                    FROM chunks
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (query_vector, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, chunk_text, metadata, embedding <=> %s AS distance
                    FROM chunks
                    WHERE metadata->>'doc_type' = %s
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (query_vector, doc_type, limit),
                )
            rows = cursor.fetchall()
    finally:
        _release_connection(pool, connection)

    results: list[dict] = []

    for row in rows:
        chunk_id, chunk_text, metadata, distance = row

        if distance is None or distance > config.retrieval.similarity_threshold:
            continue

        results.append(
            {
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "metadata": metadata,
                "distance": float(distance),
                "confidence": _distance_to_confidence(float(distance)),
            }
        )

    return results