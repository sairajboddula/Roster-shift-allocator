"""Custom exceptions and global exception handlers."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotAuthenticatedException(Exception):
    """Raised by UI dependencies when the user is not logged in."""
    def __init__(self, redirect_url: str = "/login"):
        self.redirect_url = redirect_url
        super().__init__(redirect_url)


class RosterException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundException(RosterException):
    """Raised when a resource is not found."""
    def __init__(self, resource: str, resource_id):
        super().__init__(f"{resource} with id={resource_id} not found.", status_code=404)


class ConflictException(RosterException):
    """Raised when a scheduling conflict cannot be resolved."""
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationException(RosterException):
    """Raised for domain-level validation errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach exception handlers to the FastAPI app."""

    @app.exception_handler(NotAuthenticatedException)
    async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException):
        return RedirectResponse(url=exc.redirect_url, status_code=302)

    @app.exception_handler(RosterException)
    async def roster_exception_handler(request: Request, exc: RosterException):
        logger.warning("RosterException: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": type(exc).__name__},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("ValueError: %s", str(exc))
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "type": "ValueError"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error.", "type": type(exc).__name__},
        )
