from typing import Any, Optional


class AppException(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, detail: Optional[Any] = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"


class AuthenticationError(AppException):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(AppException):
    status_code = 403
    code = "authorization_error"


class ConflictError(AppException):
    status_code = 409
    code = "conflict"


class RateLimitError(AppException):
    status_code = 429
    code = "rate_limit_exceeded"

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class QuotaExceededError(AppException):
    status_code = 402
    code = "quota_exceeded"


class ExternalAPIError(AppException):
    status_code = 502
    code = "external_api_error"


class ValidationError(AppException):
    status_code = 422
    code = "validation_error"
