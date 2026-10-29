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

    def __init__(self, message, status_code=None, reason=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


class UnauthorizedException(APIException):
    """This exception is thrown whenever the api returns a 401 unauthorized
    response."""



class TooManyRequestsException(APIException):
    """This exception is thrown whenever the api returns a 429 too many
    requests response."""



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

