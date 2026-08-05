"""
Real end-to-end integration test for the cache-aware answer_question() pipeline.
Hits real Groq, real Redis (Upstash), real Neon Postgres, real embedding model.

Run with:
    pytest -m integration -s tests/test_answer_cache_integration.py
"""

import time
import uuid

import psycopg2
import pytest

from src.agents.llm_router import answer_question
from src.config.settings import get_settings


@pytest.mark.integration
def test_answer_question_real_cache_hit_then_miss_and_db_persistence():
    # Unique suffix guarantees this exact question has never been cached
    # before, so the first call is a guaranteed real miss — not an artifact
    # of a previous test run still sitting in Redis within the 24h TTL.
    unique_marker = uuid.uuid4().hex[:8]
    question = f"My maize leaves have grey rectangular spots, what's wrong? [{unique_marker}]"
    lat, lon = 0.5143, 35.2698

    print(f"\n[TEST] Question: {question}")

    # --- First call: expect a real cache MISS ---
    start_1 = time.perf_counter()
    result_1 = answer_question(question, lat, lon, audience="farmer", language="en")
    elapsed_1 = time.perf_counter() - start_1

    print(f"[TEST] First call — cache_hit={result_1['cache_hit']} — took {elapsed_1:.2f}s")
    print(f"[TEST] Answer (first call):\n{result_1['answer']}\n")

    assert result_1["cache_hit"] is False

    # --- Second call, same question: expect a real cache HIT ---
    start_2 = time.perf_counter()
    result_2 = answer_question(question, lat, lon, audience="farmer", language="en")
    elapsed_2 = time.perf_counter() - start_2

    print(f"[TEST] Second call — cache_hit={result_2['cache_hit']} — took {elapsed_2:.2f}s")

    assert result_2["cache_hit"] is True
    assert result_2["answer"] == result_1["answer"]
    assert elapsed_2 < elapsed_1, (
        f"Expected cache hit ({elapsed_2:.2f}s) to be faster than the miss "
        f"({elapsed_1:.2f}s) — if not, caching isn't actually saving time."
    )

    print(
        f"[TEST] Speedup: {elapsed_1:.2f}s -> {elapsed_2:.2f}s "
        f"({elapsed_1 / max(elapsed_2, 0.001):.1f}x faster)"
    )

    # --- Confirm both calls actually produced rows in query_logs ---
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT query_text, route_taken, cache_hit, latency_ms, created_at
                FROM query_logs
                WHERE query_text = %s
                ORDER BY created_at ASC
                """,
                (question,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    print(f"\n[TEST] query_logs rows found for this question: {len(rows)}")
    for row in rows:
        print(f"[TEST]   {row}")

    assert len(rows) == 2, (
        f"Expected exactly 2 query_logs rows (one miss, one hit) for this "
        f"question, found {len(rows)} — logging isn't persisting correctly."
    )

    cache_hit_flags = sorted(row[2] for row in rows)
    assert cache_hit_flags == [False, True], (
        "Expected one cache_hit=False row and one cache_hit=True row in query_logs."
    )