"""
Tests for the LLM-based router.

Run unit test only:
    pytest tests/test_llm_router.py

Run integration test (hits real Groq + Neon):
    pytest -m integration -s tests/test_llm_router.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.llm_router import route_and_execute, synthesize_answer


def test_route_and_execute_calls_diagnose_symptom_when_model_chooses_it():
    fake_diagnosis_result = [
        {
            "id": "GLS",
            "common_name": "Grey Leaf Spot",
            "category": "fungal_disease",
            "symptom_description": "Rectangular grey lesions...",
            "disambiguation_notes": "...",
            "recommended_action": "Resistant varieties, crop rotation.",
            "soil_related": False,
            "confidence": 0.87,
        }
    ]

    fake_response = MagicMock()
    fake_response.tool_calls = [
        {
            "name": "diagnose_symptom",
            "args": {"symptom_description": "grey rectangular spots on leaves"},
        }
    ]

    with patch("src.agents.llm_router.get_llm") as mock_get_llm, patch(
        "src.agents.llm_router.search_diagnosis", return_value=fake_diagnosis_result
    ) as mock_search_diagnosis, patch(
        "src.agents.llm_router.log_query"
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = fake_response
        mock_get_llm.return_value = mock_llm

        result = route_and_execute(
            "My maize is very short and its not growing evenly on the field, what's wrong?",
            lat=0.5143,
            lon=35.2698,
        )

    mock_search_diagnosis.assert_called_once_with("grey rectangular spots on leaves")
    assert "diagnose_symptom" in result["tools_invoked"]
    assert result["tool_results"]["diagnose_symptom"] == fake_diagnosis_result
    assert result["diagnosis_results"] == fake_diagnosis_result


@pytest.mark.integration
def test_route_and_execute_and_synthesize_end_to_end():
    question = "My maize has grey rectangular spots on leaves, what's wrong?"

    result = route_and_execute(question, lat=0.5143, lon=35.2698)

    print("\n[DEBUG] Tools invoked:", result["tools_invoked"])
    for entry in result["diagnosis_results"]:
        print(
            f"[DEBUG] Diagnosis candidate: {entry.get('common_name')} "
            f"(confidence={entry.get('confidence'):.3f})"
        )
    for entry in result["chunk_results"]:
        print(f"[DEBUG] Chunk confidence={entry.get('confidence'):.3f}")

    answer = synthesize_answer(question, result["tool_results"], audience="expert", language="en")
    print("\n[DEBUG] Final answer:\n", answer)

    assert answer
    assert "diagnose_symptom" in result["tools_invoked"]