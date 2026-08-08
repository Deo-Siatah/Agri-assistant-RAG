from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, Request

from src.api.middleware.request_logging import get_request_id
from src.api.schemas.request import AskRequest
from src.api.schemas.response import AskResponse


logger = logging.getLogger(__name__)

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, request: Request) -> AskResponse:
    request_id = get_request_id(request)
    session_id = payload.session_id or str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        from src.agents.llm_router import answer_question

        result = answer_question(
            payload.question,
            payload.lat,
            payload.lon,
            audience=payload.audience,
            language=payload.language,
            request_id=request_id,
            session_id=session_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "ask_error request_id=%s error_type=%s error_message=%s",
            request_id,
            type(exc).__name__,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your question. Please try again.",
        ) from exc

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    return AskResponse(
        answer=result["answer"],
        tools_invoked=list(result.get("tools_invoked", [])),
        cache_hit=bool(result.get("cache_hit", False)),
        latency_ms=latency_ms,
        request_id=request_id,
        session_id=session_id,
    )
