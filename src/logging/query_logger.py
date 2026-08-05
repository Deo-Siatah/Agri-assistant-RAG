from __future__ import annotations

import psycopg2
import psycopg2.extras

from src.config.settings import get_settings


def _build_diagnosis_scores(entries: list[dict]) -> dict[str, float]:
    return {str(entry["id"]): entry["confidence"] for entry in entries}


def _build_chunk_scores(entries: list[dict]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for idx, entry in enumerate(entries):
        metadata = entry.get("metadata") or {}
        chunk_key = metadata.get("chunk_id", entry.get("chunk_id", idx))
        scores[str(chunk_key)] = entry["confidence"]
    return scores


def _should_mark_low_confidence(
    diagnosis_results: list[dict],
    chunk_results: list[dict],
    confidence_floor: float,
) -> bool:
    confidence_values = [
        float(entry.get("confidence", 0.0))
        for entry in diagnosis_results + chunk_results
    ]
    if not confidence_values:
        return True
    return max(confidence_values) < confidence_floor


def log_query(
    query_text: str,
    route_taken: str,
    cache_hit: bool,
    diagnosis_results: list[dict],
    chunk_results: list[dict],
    weather_used: bool,
    soil_used: bool,
    latency_ms: int,
    request_id: str | None = None,
    confidence_floor: float = 0.5,
) -> None:
    diagnosis_scores = _build_diagnosis_scores(diagnosis_results)
    chunk_scores = _build_chunk_scores(chunk_results)
    low_confidence = _should_mark_low_confidence(
        diagnosis_results,
        chunk_results,
        confidence_floor,
    )

    try:
        settings = get_settings()
        connection = psycopg2.connect(settings.database_url)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO query_logs (
                        query_text,
                        route_taken,
                        cache_hit,
                        diagnosis_scores,
                        chunk_scores,
                        weather_used,
                        soil_used,
                        latency_ms,
                        request_id,
                        low_confidence
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        query_text,
                        route_taken,
                        cache_hit,
                        psycopg2.extras.Json(diagnosis_scores),
                        psycopg2.extras.Json(chunk_scores),
                        weather_used,
                        soil_used,
                        latency_ms,
                        request_id,
                        low_confidence,
                    ),
                )
            connection.commit()
        finally:
            connection.close()
    except Exception as exc:
        print(f"[WARN] Failed to log query: {exc}")