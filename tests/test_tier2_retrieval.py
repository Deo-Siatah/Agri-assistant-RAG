"""Integration test for tier 2 chunk retrieval.

Run with:
    pytest -m integration -s tests/test_tier2_retrieval.py
"""

import pytest
import time
from src.retrieval.tier2_retrieval import search_chunks


@pytest.mark.integration
def test_search_chunks_finds_pest_disease_reference_chunk():
    query = "common maize diseases"
    print("\n[DEBUG] Running search_chunks with query:", query)

    # First call
    start1 = time.perf_counter()
    results1 = search_chunks(query)
    elapsed1 = time.perf_counter() - start1
    print(f"[DEBUG] First call elapsed time: {elapsed1:.3f}s")
    print("[DEBUG] Raw results count (first call):", len(results1))
    for idx, item in enumerate(results1, start=1):
        print(f"[DEBUG] Result {idx}:")
        print("   Metadata:", item.get("metadata"))
        print("   Document snippet:", str(item.get("chunk_text"))[:200], "...")

    # Second call (should be faster if cache is working)
    start2 = time.perf_counter()
    results2 = search_chunks(query)
    elapsed2 = time.perf_counter() - start2
    print(f"[DEBUG] Second call elapsed time: {elapsed2:.3f}s")
    print("[DEBUG] Raw results count (second call):", len(results2))

    assert results1
    assert any(
        item["metadata"].get("doc_type") == "pest_disease_reference"
        for item in results1
    )
    print("[DEBUG] Test assertion passed: pest_disease_reference found")
