"""Turn exceptions into the API's single error envelope: ``{"error": {"code", "message"}}``."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from drive_text_extractor.domain import errors

logger = logging.getLogger(__name__)

_STATUS_BY_ERROR: dict[type[errors.DomainError], int] = {
    errors.InvalidLinkError: status.HTTP_400_BAD_REQUEST,
    errors.InvalidSelectionError: status.HTTP_400_BAD_REQUEST,
    errors.UnsupportedLanguageError: status.HTTP_400_BAD_REQUEST,
    errors.FolderNotFoundError: status.HTTP_404_NOT_FOUND,
    errors.FileNotAccessibleError: status.HTTP_404_NOT_FOUND,
    errors.JobNotFoundError: status.HTTP_404_NOT_FOUND,
    errors.RateLimitedError: status.HTTP_429_TOO_MANY_REQUESTS,
    errors.SourceUnavailableError: status.HTTP_502_BAD_GATEWAY,
    errors.SourceNotConfiguredError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def status_for(error: errors.DomainError) -> int:
    """HTTP status of the closest mapped ancestor; unmapped domain errors are server errors."""
    for cls in type(error).__mro__:
        if cls in _STATUS_BY_ERROR:
            return _STATUS_BY_ERROR[cls]
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


async def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, errors.DomainError)
    return error_response(status_for(exc), exc.code, exc.message)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
    detail = first.get("msg", "Invalid request.")
    message = f"{field}: {detail}" if field else detail
    return error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_request", message)


async def _unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "Unexpected server error."
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(errors.DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unexpected_error)
