import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.access")

_SKIP_PATHS = {"/health", "/metrics", "/favicon.ico"}


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "request",
            extra={
                "ctx_request_id": request_id,
                "ctx_method": request.method,
                "ctx_path": request.url.path,
                "ctx_status": response.status_code,
                "ctx_duration_ms": duration_ms,
                "ctx_user_agent": request.headers.get("user-agent", ""),
            },
        )
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Duration-Ms"] = str(duration_ms)
        return response
