"""
Core Jama Connect Client API class

This module contains core classes for interacting with the Jama Connect API
"""

__all__ = ["JamaClient", "bound_retry_after"]

import json
import logging
import math
import ssl
import time
from threading import Lock

import httpx
import urllib3
from httpx import Response

from py_jama_client.constants import (
    DEFAULT_ALLOWED_RESULTS_PER_PAGE,
    DEFAULT_RETRY_AFTER_SECONDS,
    MAX_RETRY_AFTER_SECONDS,
    MAX_THROTTLE_WAITS,
    MIN_RETRY_AFTER_SECONDS,
)
from py_jama_client.exceptions import (
    AlreadyExistsException,
    APIClientException,
    APIException,
    APIServerException,
    CoreException,
    ResourceNotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
    UnauthorizedTokenException,
)
from py_jama_client.response import ClientResponse

__DEBUG__ = False

# disable warnings for ssl verification
urllib3.disable_warnings()

py_jama_client_logger = logging.getLogger("py_jama_client")


def bound_retry_after(seconds: float | None) -> float:
    """Wait for a 429: Retry-After clamped to [MIN, MAX], or the default."""
    if seconds is None:
        return DEFAULT_RETRY_AFTER_SECONDS
    if seconds > MAX_RETRY_AFTER_SECONDS:
        py_jama_client_logger.warning(
            f"Server asked to wait {seconds:.0f}s (Retry-After); "
            f"waiting {MAX_RETRY_AFTER_SECONDS:.0f}s instead"
        )
        return MAX_RETRY_AFTER_SECONDS
    return max(MIN_RETRY_AFTER_SECONDS, seconds)


class JamaClient:
    """
    Base client class
    """

    session_class = httpx.Client

    def __init__(
        self,
        host: str,
        credentials: tuple[str, str] = ("username|client_id", "password|client_secret"),
        api_version: str = "/rest/v1/",
        oauth: bool = False,
        verify: bool | str | ssl.SSLContext = True,
        timeout: int = 30,
    ):
        """
        Args:
            host: The host name of the Jama Connect server
            credentials: A tuple of username and password or client_id and
                client_secret
            api_version: The version of the Jama Connect API to use
            oauth: A boolean to indicate if OAuth is being used. Must be set
                to true if credentials are client id/secret pair.
            verify: SSL certificates (a.k.a CA bundle) used to verify the
                identity of requested hosts. Either True (default CA bundle),
                a path to an SSL certificate file, an ssl.SSLContext, or False.
            timeout: The timeout for the session
        """
        # Instance variables
        self._api_version = api_version
        self._host_name = host + self._api_version
        self._credentials = credentials
        self._oauth = oauth
        self._verify = verify
        self._session = self.session_class(verify=verify, timeout=timeout)

        # Setup OAuth if needed.
        if self._oauth:
            self._token_host = host + "/rest/oauth/token"
            self._token = None
            self._oauth_token_lock = Lock()
            self._get_fresh_token()

    def get_available_endpoints(self):
        try:
            response = self._session.get(self._host_name, auth=self._credentials)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def close(self) -> None:
        """Method to close underlying session"""
        self._session.close()

    def delete(self, resource: str, **kwargs):
        """This method will perform a delete operation on the specified
        resource"""
        url = self._host_name + resource

        if self._oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.delete(url, **kwargs)

        return self._session.delete(url, auth=self._credentials, **kwargs)

    def get(self, resource: str, params: dict | None = None, **kwargs):
        """This method will perform a get operation on the specified
        resource"""
        url = self._host_name + resource

        if self._oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.get(url, params=params, **kwargs)

        return self._session.get(url, auth=self._credentials, params=params, **kwargs)

    def patch(
        self, resource: str, params: dict | None = None, data=None, json=None, **kwargs
    ):
        """This method will perform a patch operation to the specified
        resource"""
        url = self._host_name + resource

        if self._oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.patch(
                url, params=params, data=data, json=json, **kwargs
            )

        return self._session.patch(
            url, auth=self._credentials, params=params, data=data, json=json, **kwargs
        )

    def post(
        self, resource: str, params: dict | None = None, data=None, json=None, **kwargs
    ):
        """This method will perform a post operation to the specified
        resource."""
        url = self._host_name + resource

        if self._oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.post(
                url, params=params, data=data, json=json, **kwargs
            )

        return self._session.post(
            url, auth=self._credentials, params=params, data=data, json=json, **kwargs
        )

    def put(
        self, resource: str, params: dict | None = None, data=None, json=None, **kwargs
    ):
        """This method will perform a put operation to the specified
        resource"""
        url = self._host_name + resource

        if self._oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.put(
                url, data=data, params=params, json=json, **kwargs
            )

        return self._session.put(
            url, auth=self._credentials, data=data, params=params, json=json, **kwargs
        )

    def _check_oauth_token(self):
        with self._oauth_token_lock:
            if self._token is None:
                self._get_fresh_token()
                return

            time_elapsed = time.time() - self._token_acquired_at
            time_remaining = self._token_expires_in - time_elapsed
            if time_remaining < 60:
                # if less than a minute remains, just get another token.
                self._get_fresh_token()

    def _get_fresh_token(self):
        """This method will fetch a new oauth bearer token from the oauth
        token server."""
        data = {"grant_type": "client_credentials"}

        # By getting the system time before we get the token we avoid a
        # potential bug where the token may be expired.
        time_before_request = time.time()

        # Post to the token server, check if authorized
        try:
            response = httpx.post(
                self._token_host,
                auth=self._credentials,
                data=data,
                verify=self._verify,
            )
            response.raise_for_status()
        except httpx.HTTPError as err:
            raise UnauthorizedTokenException(f"Unable to fetch token: {err}")

        # If success get relevant data
        if response.status_code in [200, 201]:
            try:
                response_json = response.json()
                self._token = response_json["access_token"]
                self._token_expires_in = response_json["expires_in"]
            except (ValueError, KeyError, TypeError) as err:
                raise UnauthorizedTokenException(
                    f"Unable to fetch token: unusable response body: {err!r}"
                )
            self._token_acquired_at = math.floor(time_before_request)

        else:
            py_jama_client_logger.error("Failed to retrieve OAuth Token")
            raise UnauthorizedTokenException(
                f"Unable to fetch token: unexpected status {response.status_code}"
            )

    def _add_auth_header(self, **kwargs):
        assert self._token is not None
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["Authorization"] = "Bearer " + self._token
        return headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._session.close()

    def get_all(
        self,
        resource,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will get all of the resources specified by the resource
        parameter, if an id or some other parameter is required for the
        resource, include it in the params parameter.
        Returns a single JSON array with all of the retrieved items.
        """

        if allowed_results_per_page < 1 or allowed_results_per_page > 50:
            raise ValueError("Allowed results per page must be between 1 and 50")

        start_index = 0
        total_results = float("inf")
        throttle_waits = 0

        data, meta, links, linked = [], {}, {}, {}  # type: ignore[var-annotated]
        while len(data) < total_results:
            try:
                page = self.get_page(
                    resource,
                    start_index,
                    params=params,
                    allowed_results_per_page=allowed_results_per_page,
                    **kwargs,
                )
            except TooManyRequestsException as err:
                throttle_waits += 1
                if throttle_waits > MAX_THROTTLE_WAITS:
                    raise
                wait = bound_retry_after(err.retry_after)
                py_jama_client_logger.info(f"Throttled (429); waiting {wait:.1f}s")
                time.sleep(wait)
                continue
            throttle_waits = 0

            meta.update(page.meta)
            links.update(page.links)

            for item_type_key, page_items in page.linked.items():
                linked.setdefault(item_type_key, {}).update(page_items)
            if not page.data:
                break
            page_info = page.meta.get("pageInfo")
            if page_info:
                start_index = (page_info.get("startIndex", 0)
                               + allowed_results_per_page)
                total_results = page_info.get("totalResults", total_results)
            else:
                total_results = 0
                break
            data.extend(page.data)

        return ClientResponse(meta, links, linked, data)

    def get_page(
        self,
        resource,
        start_at,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return one page of results from the specified
        resource type.
        Pass any needed parameters along
        The response object will be returned
        """
        pagination = {"startAt": start_at, "maxResults": allowed_results_per_page}

        if params is None:
            params = pagination
        else:
            params = params.copy()
            params.update(pagination)

        try:
            response = self.get(resource, params=params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    @staticmethod
    def handle_response_status(response: Response):
        """
        Utility method for checking http status codes.
        If the response code is not in the 200 range, An exception will be
        thrown.
        """

        status = response.status_code

        if status in range(200, 300):
            return status

        if status in range(400, 500):
            """These are client errors. It is likely that something is wrong
            with the request."""

            response_message = "No Response"

            try:
                response_json = json.loads(response.text)
                response_message = response_json.get("meta").get("message")

            except json.JSONDecodeError:
                pass

            # Log the error
            py_jama_client_logger.error(
                f"API Client Error. Status: {status} Message: {response_message}"
            )

            if response_message is not None and "already exists" in response_message:
                raise AlreadyExistsException(
                    "Entity already exists.",
                    status_code=status,
                    reason=response_message,
                )

            if status == 401:
                raise UnauthorizedException(
                    "Unauthorized: check credentials and permissions.  "
                    f"API response message {response_message}",
                    status_code=status,
                    reason=response_message,
                )

            if status == 404:
                raise ResourceNotFoundException(
                    "Resource not found. check host url.",
                    status_code=status,
                    reason=response_message,
                )

            if status == 429:
                raise TooManyRequestsException(
                    "Too many requests.  API throttling limit reached, or "
                    "system under maintenance.",
                    status_code=status,
                    reason=response_message,
                    headers=response.headers,
                )

            raise APIClientException(
                f"{status} {response.reason_phrase} Client Error.  Bad Request.  API response message: {response_message}",
                status_code=status,
                reason=response_message,
            )

        if status in range(500, 600):
            """These are server errors and network errors."""

            # Log The Error
            py_jama_client_logger.error(
                f"{status} Server error. {response.reason_phrase}"
            )
            raise APIServerException(
                f"{status} Server Error.",
                status_code=status,
                reason=response.reason_phrase,
            )

        # Catch anything unexpected
        py_jama_client_logger.error(
            f"{status} error. {response.reason_phrase}"
        )
        raise APIException(
            f"{status} error", status_code=status, reason=response.reason_phrase
        )
