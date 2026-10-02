from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}


class NotFoundError(DomainError):
    def __init__(self, message: str, code: str = "NOT_FOUND", detail: dict[str, Any] | None = None) -> None:
        super().__init__(message, code=code, status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(DomainError):
    def __init__(self, message: str, code: str = "CONFLICT", detail: dict[str, Any] | None = None) -> None:
        super().__init__(message, code=code, status_code=status.HTTP_409_CONFLICT, detail=detail)


class AuthenticationError(DomainError):
    def __init__(self, message: str = "Invalid credentials", code: str = "UNAUTHORIZED") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(DomainError):
    def __init__(self, message: str = "Permission denied", code: str = "FORBIDDEN") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_403_FORBIDDEN)


class BudgetExceededError(DomainError):
    def __init__(self, message: str = "Run token/cost budget exceeded", code: str = "BUDGET_EXCEEDED") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class SSRFSecurityError(DomainError):
    def __init__(self, message: str = "Target address blocked by security policy", code: str = "SSRF_BLOCKED") -> None:
        super().__init__(message, code=code, status_code=status.HTTP_400_BAD_REQUEST)


def setup_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        content = {
            "type": f"https://agentpulse.dev/errors/{exc.code.lower()}",
            "title": exc.code,
            "status": exc.status_code,
            "detail": exc.message,
            "instance": str(request.url),
            "errors": exc.detail
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            media_type="application/problem+json"
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        content = {
            "type": "https://agentpulse.dev/errors/validation-error",
            "title": "VALIDATION_ERROR",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "Request payload validation failed",
            "instance": str(request.url),
            "errors": exc.errors()
        }
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=content,
            media_type="application/problem+json"
        )
