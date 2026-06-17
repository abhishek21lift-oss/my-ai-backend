import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from exceptions.app_exceptions import AppException, RateLimitError

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, detail=None) -> dict:
    body = {"error": {"code": code, "message": message}}
    if detail is not None:
        body["error"]["detail"] = detail
    return body


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        headers = {}
        if isinstance(exc, RateLimitError):
            headers["Retry-After"] = str(exc.retry_after)
        logger.warning(
            "App exception",
            extra={"ctx_code": exc.code, "ctx_path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.detail),
            headers=headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("http_error", str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(x) for x in e["loc"]), "msg": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body("validation_error", "Request validation failed", errors),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception", extra={"ctx_path": request.url.path})
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", "An unexpected error occurred"),
        )
