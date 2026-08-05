"""Integration test for tier 1 diagnosis retrieval.

Run with:
    pytest -m integration tests/test_tier1_retrieval.py
"""

import pytest

from src.retrieval.tier1_retrieval import search_diagnosis


@pytest.mark.integration
def test_search_diagnosis_returns_gls_near_top():

    results = search_diagnosis("grey rectangular spots on leaves")

    assert results
    assert results[0]["id"] == "GLS" or any(
        item["id"] == "GLS" for item in results[:3]
    )