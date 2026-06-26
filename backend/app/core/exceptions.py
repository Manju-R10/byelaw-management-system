"""Application exception hierarchy and FastAPI exception handlers.

All API errors are returned in a single, consistent JSON envelope so the frontend
can handle them uniformly:

    {
        "success": false,
        "error": {"code": "AUTHENTICATION_FAILED", "message": "Invalid credentials."}
    }
"""
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base class for all expected, handled application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    default_message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message or self.default_message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"
    default_message = "Authentication failed."


class AuthorizationError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "AUTHORIZATION_FAILED"
    default_message = "You do not have permission to perform this action."


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    default_message = "The requested resource was not found."


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"
    default_message = "The request conflicts with the current state of the resource."


class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    default_message = "The request was invalid."


class ValidationException(AppException):
    status_code = 422  # Unprocessable Content
    error_code = "VALIDATION_ERROR"
    default_message = "The submitted data failed validation."


def _error_response(status_code: int, error_code: str, message: str, details: Any = None) -> JSONResponse:
    payload: dict[str, Any] = {
        "success": False,
        "error": {"code": error_code, "message": message},
    }
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def _handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        # Client errors (4xx) are expected; log at WARNING. Server errors at ERROR.
        log = logger.warning if exc.status_code < 500 else logger.error
        log("AppException on %s %s -> %s: %s", request.method, request.url.path, exc.error_code, exc.message)
        return _error_response(exc.status_code, exc.error_code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        return _error_response(
            422,  # Unprocessable Content
            "VALIDATION_ERROR",
            "One or more fields failed validation.",
            details=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(SQLAlchemyError)
    async def _handle_db_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # Never leak internal DB details to clients.
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "DATABASE_ERROR",
            "A database error occurred while processing the request.",
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
        )
