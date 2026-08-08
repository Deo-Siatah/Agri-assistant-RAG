from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Input payload for an agronomy question request."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The user's natural-language agriculture question.",
    )
    lat: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude of the farm or observation point in decimal degrees.",
    )
    lon: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude of the farm or observation point in decimal degrees.",
    )
    audience: Literal["farmer", "expert"] = Field(
        default="farmer",
        description="Target audience level that controls response style and depth.",
    )
    language: Literal["en", "sw"] = Field(
        default="en",
        description="Preferred output language for the generated answer.",
    )
    session_id: Optional[str] =Field(
        default=None,
        description="Optional session ID to maintain conversation context across follow-up questions. "
                    "If omitted, a new session is started and its ID is returned in the response."
    )