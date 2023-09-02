from typing import Any, Dict
from starlette.exceptions import HTTPException as StarletteHTTPException

from util import response


class APIError(Exception):
    status_code: int = None
    message: str = None
    error_code: int = None
    headers: dict = None

    def __init__(
            self,
            message: str = None,
            *,
            status_code: int = None,
            error_code: int = None,
            headers: Dict[str, Any] = None,
    ):
        if not message and not self.message:
            raise ValueError('`message` is required')

        if not status_code and not self.status_code:
            raise ValueError('`status_code` is required')

        self.status_code = status_code or self.status_code
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.headers = headers or self.headers


class AuthorizationError(APIError):
    status_code = 401


class PermissionError(APIError):
    status_code = 403


class BadRequestError(APIError):
    status_code = 400


class NotFoundError(APIError):
    status_code = 404


class ServerError(APIError):
    status_code = 500


class UnavailableError(APIError):
    status_code = 503


def user_exception_handler(request, exc: APIError):
    return response(
        http_status=exc.status_code,
        error=exc.message,
        error_code=exc.error_code,
    )


def global_exception_handler(request, exc: Exception):
    return response(
        http_status=500,
        error='Internal Server Error',
    )


def install_exception_handlers(app):
    app.add_exception_handler(APIError, user_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    app.exception_handlers.pop(StarletteHTTPException)
