from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AskResponse(BaseModel):
    """Standard response payload for the ask endpoint."""

    answer: str = Field(description="Generated answer returned to the client.")
    tools_invoked: list[str] = Field(
        description="Ordered list of internal tools/services used to generate the answer."
    )
    cache_hit: bool = Field(
        description="Whether the answer was returned directly from cache."
    )
    latency_ms: int = Field(
        description="End-to-end request latency in milliseconds."
    )
    request_id: str = Field(
        description="Server-generated request identifier for tracing and support."
    )
    session_id: str = Field(
        description="Conversation session identifier used to persist follow-up context."
    )


class HealthResponse(BaseModel):
    """Health check response for service and dependency status."""

    status: Literal["ok", "degraded", "error"] = Field(
        description="Overall health state derived from dependency checks."
    )
    checks: dict[str, str] = Field(
        description="Per-dependency status map, for example database and cache checks."
    )
