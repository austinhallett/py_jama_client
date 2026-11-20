import math
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _parse_retry_after(
    value: str | None, now: datetime | None = None
) -> float | None:
    if not value:
        return None

    try:
        delay = float(value)
    except ValueError:
        retry_at = _parse_http_date(value)
        if retry_at is None:
            return None

        current_time = now or datetime.now(UTC)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=UTC)
        return max(0.0, (retry_at - current_time).total_seconds())

    return max(0.0, delay) if math.isfinite(delay) else None


class CoreException(Exception):
    """This is the base class for all exceptions raised by the Core"""

    def __init__(self, message, status_code=None, reason=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


class UnauthorizedTokenException(CoreException):
    """This exception is thrown whenever fetching the oauth token returns a
    401 unauthorized response."""



class APIException(Exception):
    """This is the base class for all exceptions raised by the JamaClient"""

    def __init__(self, message, status_code=None, reason=None, headers=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason
        self.headers = headers


class UnauthorizedException(APIException):
    """This exception is thrown whenever the api returns a 401 unauthorized
    response."""



class TooManyRequestsException(APIException):
    """This exception is thrown whenever the api returns a 429 too many
    requests response.

    Attributes:
        retry_after: Retry-After in seconds as of creation (dates measured
            from the Date header), or None if absent or unparseable.
    """

    def __init__(self, message, status_code=None, reason=None, headers=None):
        super().__init__(
            message, status_code=status_code, reason=reason, headers=headers
        )
        lookup = httpx.Headers(headers or {})
        self.retry_after: float | None = _parse_retry_after(
            lookup.get("retry-after"),
            now=_parse_http_date(lookup.get("date")),
        )



class ResourceNotFoundException(APIException):
    """This exception is raised whenever the api returns a 404 not found
    response."""



class AlreadyExistsException(APIException):
    """This exception is thrown when the API returns a 400 response with a
    message that the resource already exists."""



class APIClientException(APIException):
    """This exception is thrown whenever a unknown 400 error is encountered."""



class APIServerException(APIException):
    """This exception is thrown whenever an unknown 500 response is
    encountered."""

