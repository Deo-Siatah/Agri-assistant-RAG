from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) and request_id else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()
        response: Response | None = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            logger.error(
                "request_error request_id=%s method=%s path=%s error_type=%s error_message=%s",
                request_id,
                request.method,
                request.url.path,
                type(exc).__name__,
                exc,
            )
            raise
        finally:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "request_access request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
