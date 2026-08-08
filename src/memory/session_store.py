"""
Redis-backed short-term conversational memory.

Concept mirrors LangGraph's thread + checkpointer: session_id is the
"thread", Redis is the "checkpointer" persisting turns against it.

Storage shape (one JSON blob per session, via existing cache_get/cache_set):
{
    "summary": str | None,          # rolling summary of older turns, or None
    "turns": [                       # recent turns kept verbatim
        {"role": "user" | "assistant", "content": str, "timestamp": float}
    ]
}

TTL is sliding — refreshed on every append, so an active conversation never
expires mid-use, but an idle one cleans up automatically after SESSION_TTL_SECONDS.
"""

from __future__ import annotations

import time

from src.cache.cache_utils import cache_get, cache_set
from src.chains.llm import get_llm

SESSION_TTL_SECONDS = 12 * 60 * 60  # 12 hours idle expiry
KEEP_RECENT_TURNS = 6  # roughly last 3 exchanges kept verbatim before summarizing
SUMMARIZE_TRIGGER_TURNS = 8  # summarize once history grows past this many turns


def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


def get_session_context(session_id: str) -> dict:
    """
    Returns {"summary": str|None, "turns": list[dict]} for this session.
    Returns an empty structure if the session doesn't exist or Redis is down
    — memory is an enhancement, never a hard dependency for answering.
    """
    context = cache_get(_session_key(session_id))
    if context is None:
        return {"summary": None, "turns": []}
    return context


def append_turn(session_id: str, role: str, content: str) -> None:
    """
    Appends one turn (role: "user" or "assistant") to the session, refreshes
    the sliding TTL, and triggers summarization if the turn count has grown
    past the threshold.
    """
    context = get_session_context(session_id)
    context["turns"].append(
        {"role": role, "content": content, "timestamp": time.time()}
    )

    cache_set(_session_key(session_id), context, ttl_seconds=SESSION_TTL_SECONDS)

    if len(context["turns"]) > SUMMARIZE_TRIGGER_TURNS:
        maybe_summarize(session_id)


def maybe_summarize(session_id: str, keep_recent: int = KEEP_RECENT_TURNS) -> None:
    """
    Collapses older turns into a rolling summary, keeping only the most
    recent `keep_recent` turns verbatim. No-op if there's nothing old enough
    to summarize yet.
    """
    context = get_session_context(session_id)
    turns = context["turns"]

    if len(turns) <= keep_recent:
        return

    turns_to_summarize = turns[:-keep_recent]
    turns_to_keep = turns[-keep_recent:]

    existing_summary = context.get("summary")
    conversation_text = "\n".join(
        f"{t['role']}: {t['content']}" for t in turns_to_summarize
    )

    prompt = (
        "Summarize this part of an ongoing conversation between a maize "
        "farmer and an agricultural assistant, in 2-4 concise sentences. "
        "Preserve any specific diagnosis, recommendation, or key fact "
        "mentioned — this summary will be used as context for future "
        "questions in the same conversation, so do not lose important details.\n\n"
        f"{'Previous summary: ' + existing_summary + chr(10) + chr(10) if existing_summary else ''}"
        f"Conversation to summarize:\n{conversation_text}"
    )

    llm = get_llm()
    response = llm.invoke([{"role": "user", "content": prompt}])

    context["summary"] = response.content
    context["turns"] = turns_to_keep

    cache_set(_session_key(session_id), context, ttl_seconds=SESSION_TTL_SECONDS)


def build_context_messages(session_id: str) -> list[dict]:
    """
    Assembles the session's summary (if any) + recent turns into a list of
    chat messages ready to prepend before the current user question when
    calling the LLM. Returns an empty list for a brand-new session.
    """
    context = get_session_context(session_id)
    messages: list[dict] = []

    if context.get("summary"):
        messages.append(
            {
                "role": "system",
                "content": f"Summary of earlier conversation: {context['summary']}",
            }
        )

    for turn in context["turns"]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    return messages