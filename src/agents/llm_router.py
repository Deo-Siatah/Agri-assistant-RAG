"""
LLM-based intent + tool-calling router.

Replaces the keyword-based router (moved to router_legacy.py). The LLM decides
which tool(s) to call based on the user's question, tools execute, and a
second LLM call synthesizes a final answer grounded in the tool results.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import traceback

from src.cache.cache_utils import cache_get, cache_set
from src.chains.llm import get_llm
from src.chains.prompt_loader import load_synthesis_prompts
from src.logging.query_logger import log_query
from src.memory.session_store import append_turn, build_context_messages, get_session_context


logger = logging.getLogger(__name__)

# Module-level placeholders kept for test monkeypatch compatibility.
search_diagnosis = None
search_chunks = None
get_weather_summary = None
get_soil_summary = None
query_csv = None


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_pdf_knowledge",
            "description": (
                "Search general maize agronomy reference documents (research papers, "
                "extension guides) for background information not covered by the "
                "structured pest/disease diagnosis tool. Use for general questions "
                "about planting, varieties, market context, or agronomic background."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query describing what information is needed.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_symptom",
            "description": (
                "Look up a specific pest, disease, or nutrient deficiency based on "
                "a farmer's description of symptoms observed on their maize crop "
                "(e.g. leaf spots, discoloration, stunting, visible pests). Use this "
                "whenever the question describes an observed physical symptom."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptom_description": {
                        "type": "string",
                        "description": "The symptom(s) described by the farmer, in their own words.",
                    }
                },
                "required": ["symptom_description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_csv_data",
            "description": (
                "Answer questions about historical farm production data — yields, "
                "county comparisons, crop performance, rainfall correlation — from "
                "the structured production dataset."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The data question to answer from the CSV dataset.",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get current weather conditions (temperature, humidity, precipitation, "
                "wind) for the farmer's location. Use when the question involves current "
                "or recent weather, or when weather context would help assess disease risk."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude of the farm location."},
                    "lon": {"type": "number", "description": "Longitude of the farm location."},
                },
                "required": ["lat", "lon"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_soil_data",
            "description": (
                "Get soil composition data (pH, nitrogen, organic carbon, texture) for "
                "the farmer's location. Use when the question involves soil conditions, "
                "fertilizer recommendations, or when disambiguating nutrient deficiency "
                "from disease."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude of the farm location."},
                    "lon": {"type": "number", "description": "Longitude of the farm location."},
                },
                "required": ["lat", "lon"],
            },
        },
    },
]


def _execute_tool(name: str, arguments: dict, lat: float, lon: float):
    """Dispatch a single tool call to its underlying implementation."""
    if name == "search_pdf_knowledge":
        tool = globals().get("search_chunks")
        if callable(tool):
            return tool(arguments["query"])

        from src.retrieval.tier2_retrieval import search_chunks as search_chunks_impl

        return search_chunks_impl(arguments["query"])
    if name == "diagnose_symptom":
        tool = globals().get("search_diagnosis")
        if callable(tool):
            return tool(arguments["symptom_description"])

        from src.retrieval.tier1_retrieval import search_diagnosis as search_diagnosis_impl

        return search_diagnosis_impl(arguments["symptom_description"])
    if name == "query_csv_data":
        tool = globals().get("query_csv")
        if callable(tool):
            return tool(arguments["question"])

        from src.tools.csv_tool import query_csv as query_csv_impl

        return query_csv_impl(arguments["question"])
    if name == "get_weather":
        tool = globals().get("get_weather_summary")
        if callable(tool):
            return tool(arguments.get("lat", lat), arguments.get("lon", lon))

        from src.tools.weather_tool import get_weather_summary as get_weather_summary_impl

        return get_weather_summary_impl(arguments.get("lat", lat), arguments.get("lon", lon))
    if name == "get_soil_data":
        tool = globals().get("get_soil_summary")
        if callable(tool):
            return tool(arguments.get("lat", lat), arguments.get("lon", lon))

        from src.tools.soil_tool import get_soil_summary as get_soil_summary_impl

        return get_soil_summary_impl(arguments.get("lat", lat), arguments.get("lon", lon))
    raise ValueError(f"Unknown tool: {name}")


def route_and_execute(
    user_question: str,
    lat: float,
    lon: float,
    request_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """
    Ask the LLM which tool(s) to call for this question, execute them, and
    return the collected results. Logs the query regardless of outcome.
    """
    start = time.perf_counter()

    llm = get_llm()
    llm_with_tools = llm.bind_tools(TOOLS, tool_choice="auto", parallel_tool_calls=False)

    context_messages = build_context_messages(session_id) if session_id else []
    system_message_dict = {
        "role": "system",
        "content": (
            "You are an agricultural assistant specialized in maize farming in Kenya. You have access ONLY to the tools explicitly provided in this request. Do not call any tool that is not in that list. If the user's question is unrelated to maize farming, agriculture, weather, or soil, do not call any tool."
        ),
    }

    try:
        messages = [system_message_dict] + context_messages + [{"role": "user", "content": user_question}]
        response = llm_with_tools.invoke(messages)
        tool_calls = getattr(response, "tool_calls", None) or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "tool_call_invocation_failed request_id=%s error_message=%s",
            request_id,
            exc,
        )
        tool_calls = []

    tool_results: dict = {}
    tools_invoked: list[str] = []
    diagnosis_results: list[dict] = []
    chunk_results: list[dict] = []
    weather_used = False
    soil_used = False

    for call in tool_calls:
        name = call["name"]
        arguments = call.get("args", {}) or {}
        tools_invoked.append(name)

        try:
            result = _execute_tool(name, arguments, lat, lon)
            tool_results[name] = result

            if name == "diagnose_symptom":
                diagnosis_results = result or []
            elif name == "search_pdf_knowledge":
                chunk_results = result or []
            elif name == "get_weather":
                weather_used = True
            elif name == "get_soil_data":
                soil_used = True

        except Exception as exc:  # noqa: BLE001 - deliberate: one bad tool must not sink the request
            traceback.print_exc()
            tool_results[name] = {"error": str(exc)}

    # --- Deterministic auto-attachment, not left to LLM discretion ---
    # Diagnosing a symptom or pulling general agronomic reference material both
    # benefit from live environmental grounding (trigger_conditions matching),
    # so weather is always attached for these, regardless of whether the LLM
    # itself chose to call it.
    needs_weather = (
        "diagnose_symptom" in tools_invoked or "search_pdf_knowledge" in tools_invoked
    )
    if needs_weather and "get_weather" not in tools_invoked:
        try:
            weather_result = _execute_tool("get_weather", {"lat": lat, "lon": lon}, lat, lon)
            tool_results["get_weather"] = weather_result
            tools_invoked.append("get_weather")
            weather_used = True
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] weather auto-attach failed: {exc}")
            tool_results["get_weather"] = {"error": str(exc)}

    # Soil is only auto-attached when a returned diagnosis candidate is
    # actually flagged soil_related — no point fetching soil data for a
    # purely fungal/viral/pest diagnosis.
    needs_soil = any(r.get("soil_related") for r in diagnosis_results)
    if needs_soil and "get_soil_data" not in tools_invoked:
        try:
            soil_result=_execute_tool("get_soil_data", {"lat": lat, "lon": lon}, lat, lon)
            tool_results["get_soil_data"] = soil_result
            tools_invoked.append("get_soil_data")
            soil_used = True
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] soil auto-attach failed: {exc}")
            tool_results["get_soil_data"] = {"error": str(exc)}

    latency_ms = int((time.perf_counter() - start) * 1000)

    try:
        log_query(
            query_text=user_question,
            route_taken="llm_router",
            cache_hit=False,
            diagnosis_results=diagnosis_results,
            chunk_results=chunk_results,
            weather_used=weather_used,
            soil_used=soil_used,
            latency_ms=latency_ms,
            request_id=request_id,
        )
    except Exception:  # noqa: BLE001 - logging must never break the request
        traceback.print_exc()

    return {
        "tool_results": tool_results,
        "tools_invoked": tools_invoked,
        "diagnosis_results": diagnosis_results,
        "chunk_results": chunk_results,
    }


def _has_low_confidence(diagnosis_results: list[dict], chunk_results: list[dict]) -> bool:
    scores = [r.get("confidence", 1.0) for r in diagnosis_results]
    scores += [r.get("confidence", 1.0) for r in chunk_results]
    return bool(scores) and max(scores) < 0.5


def synthesize_answer(
    user_question: str,
    tool_results: dict,
    audience: str = "farmer",
    language: str = "en",
    session_id: str | None = None,
) -> str:
    """
    Produce the final natural-language answer grounded in whatever tool
    results were collected. Falls back to a direct answer if no tools ran.

    audience: "farmer" | "expert" — controls tone, vocabulary, and structure.
    language: ISO code present in src/prompts/synthesis.yaml's language map
              (e.g. "en", "sw"). Falls back to English if unrecognized.
    """
    llm = get_llm()
    context_messages = build_context_messages(session_id) if session_id else []

    if not tool_results:
        response = llm.invoke(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a maize farming assistant. If this question is unrelated "
                        "to maize agriculture, weather, soil, or farming, politely explain "
                        "that you can only help with maize farming topics and ask if they "
                        "have an agriculture-related question instead. If it IS "
                        "agriculture-related but doesn't need external data, answer it "
                        "directly and helpfully."
                    ),
                },
                *context_messages,
                {"role": "user", "content": user_question},
            ]
        )
        return response.content

    prompts = load_synthesis_prompts()

    if audience not in prompts["audience"]:
        audience = "farmer"
    if language not in prompts["language"]:
        language = "en"

    diagnosis_results = tool_results.get("diagnose_symptom", [])
    chunk_results = tool_results.get("search_pdf_knowledge", [])
    low_confidence = _has_low_confidence(
        diagnosis_results if isinstance(diagnosis_results, list) else [],
        chunk_results if isinstance(chunk_results, list) else [],
    )

    uncertainty_instruction = (
        "IMPORTANT: The retrieved information has LOW confidence scores. "
        "Clearly express uncertainty in your answer and recommend the farmer "
        "consult a local agricultural extension officer to confirm, rather "
        "than stating the diagnosis or recommendation as definite.\n\n"
        if low_confidence
        else ""
    )

    prompt = prompts["base_template"].format(
        audience_instructions=prompts["audience"][audience],
        uncertainty_instruction=uncertainty_instruction,
        question=user_question,
        tool_results=json.dumps(tool_results, indent=2, default=str),
        language_instruction=prompts["language"][language],
        structure_instruction=prompts["structure"][audience],
    )

    response = llm.invoke(context_messages + [{"role": "user", "content": prompt}])
    return response.content


# =========================================================
# Cache-aware entry point — this is what FastAPI's /ask should call.
# =========================================================

CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours — correctness safety net, not just a size cap


def _build_cache_key(question: str, lat: float, lon: float, audience: str, language: str) -> str:
    normalized = question.strip().lower()
    question_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"answer:{question_hash}:{round(lat, 2)}:{round(lon, 2)}:{audience}:{language}"


def answer_question(
    user_question: str,
    lat: float,
    lon: float,
    audience: str = "farmer",
    language: str = "en",
    request_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """
    Full pipeline entry point: checks cache first, falls through to
    routing + synthesis on a miss, and caches the result. Always logs
    to query_logs, whether it was a hit or a miss.
    """
    start = time.perf_counter()
    cache_key = _build_cache_key(user_question, lat, lon, audience, language)

    has_history = False
    if session_id:
        existing = get_session_context(session_id)
        has_history = len(existing["turns"]) > 0

    cached = None
    if not has_history:
        cached = cache_get(cache_key)

    if cached is not None:
        latency_ms = int((time.perf_counter() - start) * 1000)
        print(f"[CACHE HIT] key={cache_key} latency_ms={latency_ms}")
        answer_text = cached["answer"]

        try:
            log_query(
                query_text=user_question,
                route_taken="cache_hit",
                cache_hit=True,
                diagnosis_results=[],
                chunk_results=[],
                weather_used=False,
                soil_used=False,
                latency_ms=latency_ms,
                request_id=request_id,
            )
        except Exception:  # noqa: BLE001
            traceback.print_exc()

        if session_id is not None:
            append_turn(session_id, "user", user_question)
            append_turn(session_id, "assistant", answer_text)

        return {**cached, "cache_hit": True}

    print(f"[CACHE MISS] key={cache_key} — running full pipeline")

    routing_result = route_and_execute(
        user_question,
        lat,
        lon,
        request_id=request_id,
        session_id=session_id,
    )
    answer = synthesize_answer(
        user_question,
        routing_result["tool_results"],
        audience=audience,
        language=language,
        session_id=session_id,
    )

    payload = {
        "answer": answer,
        "tools_invoked": routing_result["tools_invoked"],
    }

    if not has_history:
        cache_set(cache_key, payload, ttl_seconds=CACHE_TTL_SECONDS)

    if session_id is not None:
        append_turn(session_id, "user", user_question)
        append_turn(session_id, "assistant", answer)

    return {**payload, "cache_hit": False}