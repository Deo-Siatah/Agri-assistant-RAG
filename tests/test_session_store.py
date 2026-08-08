"""
Tests for Redis-backed session store.

Run unit tests only:
    pytest tests/test_session_store.py

Run integration test (real Redis + real Groq summarization call):
    pytest -m integration -s tests/test_session_store.py
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.memory.session_store import (
    append_turn,
    build_context_messages,
    get_session_context,
    maybe_summarize,
)


def test_get_session_context_returns_empty_for_unknown_session():
    with patch("src.memory.session_store.cache_get", return_value=None):
        context = get_session_context("nonexistent-session")

    assert context == {"summary": None, "turns": []}


def test_append_turn_adds_to_existing_context_and_saves():
    existing = {"summary": None, "turns": [{"role": "user", "content": "hi", "timestamp": 1.0}]}

    with patch("src.memory.session_store.cache_get", return_value=existing), patch(
        "src.memory.session_store.cache_set"
    ) as mock_set:
        append_turn("session-1", "assistant", "hello back")

    saved_context = mock_set.call_args[0][1]
    assert len(saved_context["turns"]) == 2
    assert saved_context["turns"][-1]["content"] == "hello back"


def test_maybe_summarize_noop_when_turns_below_threshold():
    short_context = {
        "summary": None,
        "turns": [{"role": "user", "content": "hi", "timestamp": 1.0}] * 3,
    }

    with patch("src.memory.session_store.cache_get", return_value=short_context), patch(
        "src.memory.session_store.cache_set"
    ) as mock_set, patch("src.memory.session_store.get_llm") as mock_get_llm:
        maybe_summarize("session-1", keep_recent=6)

    mock_set.assert_not_called()
    mock_get_llm.assert_not_called()


def test_maybe_summarize_collapses_old_turns_when_above_threshold():
    long_context = {
        "summary": None,
        "turns": [
            {"role": "user", "content": f"question {i}", "timestamp": float(i)}
            for i in range(10)
        ],
    }

    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Farmer asked about several things earlier."

    with patch("src.memory.session_store.cache_get", return_value=long_context), patch(
        "src.memory.session_store.cache_set"
    ) as mock_set, patch("src.memory.session_store.get_llm", return_value=mock_llm):
        maybe_summarize("session-1", keep_recent=6)

    saved_context = mock_set.call_args[0][1]
    assert saved_context["summary"] == "Farmer asked about several things earlier."
    assert len(saved_context["turns"]) == 6
    assert saved_context["turns"][0]["content"] == "question 4"  # oldest 4 summarized away


def test_build_context_messages_includes_summary_and_turns():
    context = {
        "summary": "Diagnosed Gray Leaf Spot earlier.",
        "turns": [{"role": "user", "content": "what fertilizer should I use", "timestamp": 1.0}],
    }

    with patch("src.memory.session_store.cache_get", return_value=context):
        messages = build_context_messages("session-1")

    assert messages[0]["role"] == "system"
    assert "Gray Leaf Spot" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "what fertilizer should I use"}


@pytest.mark.integration
def test_real_append_and_summarize_end_to_end():
    """Real Redis + real Groq summarization call — proves it end to end."""
    session_id = f"test-{uuid.uuid4().hex[:8]}"

    conversation = [
        ("user", "My maize leaves have grey rectangular spots"),
        ("assistant", "This sounds like Gray Leaf Spot, a fungal disease."),
        ("user", "What should I do about it"),
        ("assistant", "Rotate crops and consider a fungicide."),
        ("user", "How long should I rotate for"),
        ("assistant", "At least 2 years with a non-host crop like beans."),
        ("user", "What fertilizer should I use now"),
        ("assistant", "Standard recommended rates for maize, given no deficiency was found."),
        ("user", "Is my area at risk of this disease right now"),
    ]

    for role, content in conversation:
        append_turn(session_id, role, content)

    context = get_session_context(session_id)
    print(f"\n[TEST] Turns remaining after summarization: {len(context['turns'])}")
    print(f"[TEST] Summary: {context['summary']}")

    assert context["summary"] is not None
    assert "Gray Leaf Spot" in context["summary"] or "gray leaf spot" in context["summary"].lower()
    assert len(context["turns"]) <= 6

    messages = build_context_messages(session_id)
    print(f"[TEST] Assembled context messages: {len(messages)}")
    assert messages[0]["role"] == "system"