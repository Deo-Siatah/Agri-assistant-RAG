from __future__ import annotations

from functools import lru_cache
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from psycopg2.pool import SimpleConnectionPool

from src.config.app_config import get_app_config
from src.config.settings import get_settings
from src.embeddings.embedding_service import get_embeddings


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


def search_diagnosis(
    symptom_description: str,
    top_k: int | None = None,
) -> list[dict]:

    config = get_app_config()
    embeddings = get_embeddings()

    # Step 1: Embed the query
    query_vector = np.array(embeddings.embed_query(symptom_description))
    print("\n[DEBUG] Symptom description:", symptom_description)
    print("[DEBUG] Query vector shape:", query_vector.shape)
    print("[DEBUG] Query vector sample:", query_vector[:10])  # show first 10 numbers

    limit = top_k if top_k is not None else config.retrieval.top_k
    print("[DEBUG] Top-K limit:", limit)

    pool, connection = _get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, common_name, category, symptom_description,
                       disambiguation_notes, recommended_action, soil_related,
                       embedding <=> %s AS distance
                FROM diagnosis_entries
                ORDER BY distance
                LIMIT %s
                """,
                (query_vector, limit),
            )
            rows = cursor.fetchall()
            print("\n[DEBUG] Raw rows fetched:", len(rows))
            for r in rows:
                print("[DEBUG] Row:", r)
    finally:
        _release_connection(pool, connection)

    results: list[dict] = []

    for row in rows:
        (
            entry_id,
            common_name,
            category,
            symptom_text,
            disambiguation_notes,
            recommended_action,
            soil_related,
            distance,
        ) = row

        print("\n[DEBUG] Processing row ID:", entry_id)
        print("[DEBUG] Distance:", distance)

        if distance is None or distance > config.retrieval.similarity_threshold:
            print("[DEBUG] Skipped due to threshold")
            continue

        result_item = {
            "id": entry_id,
            "common_name": common_name,
            "category": category,
            "symptom_description": symptom_text,
            "disambiguation_notes": disambiguation_notes,
            "recommended_action": recommended_action,
            "soil_related": soil_related,
            "distance": float(distance),
            "confidence": _distance_to_confidence(float(distance)),
        }
        print("[DEBUG] Added result:", result_item)

        results.append(result_item)

    print("\n[DEBUG] Final filtered results count:", len(results))
    return results
