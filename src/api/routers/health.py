from __future__ import annotations

import logging

import psycopg2
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.cache.redis_client import get_redis_client
from src.config.settings import get_settings
from src.api.schemas.response import HealthResponse


logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


def _truncate_message(message: str, limit: int = 100) -> str:
    compact = " ".join(message.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


@router.get("/health", response_model=HealthResponse)
def health_check() -> JSONResponse:
    checks: dict[str, str] = {}
    try:
        settings = get_settings()
        connection = psycopg2.connect(settings.database_url)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = "ok"
        finally:
            connection.close()
    except Exception as exc:  # noqa: BLE001
        checks["database"] = _truncate_message(str(exc))

    try:
        redis_client = get_redis_client()
        if redis_client is None:
            checks["redis"] = "unavailable"
        else:
            redis_client.ping()
            checks["redis"] = "ok"
    except Exception:  # noqa: BLE001
        checks["redis"] = "unavailable"

    embeddings_ok = False
    try:
        from src.embeddings.embedding_service import get_embeddings

        embeddings = get_embeddings()
        if embeddings is None:
            checks["embeddings"] = "unavailable"
        else:
            checks["embeddings"] = "ok"
            embeddings_ok = True
    except Exception as exc:  # noqa: BLE001
        checks["embeddings"] = _truncate_message(str(exc))

    if checks.get("database") != "ok" or not embeddings_ok:
        status = "error"
        http_status = 503
    elif checks.get("redis") == "unavailable":
        status = "degraded"
        http_status = 200
    else:
        status = "ok"
        http_status = 200

    logger.info(
        "health_check status=%s database=%s redis=%s embeddings=%s",
        status,
        checks.get("database"),
        checks.get("redis"),
        checks.get("embeddings"),
    )

    return JSONResponse(
        status_code=http_status,
        content=HealthResponse(status=status, checks=checks).model_dump(),
    )
