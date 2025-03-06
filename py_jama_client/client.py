"""
Core Jama Connect Client API class

This module contains core classes for interacting with the Jama Connect API
"""

__all__ = ["JamaClient"]

import json
import logging
import math
import ssl
import time
import typing
from typing import Optional, Tuple

import httpx
import urllib3
from httpx import Response

from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
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


class JamaClient:
    """
    Base client class
    """

    session_class = httpx.Client

    def __init__(
        self,
        host: str,
        credentials: Tuple[str, str] = ("username|client_id", "password|client_secret"),
        api_version: str = "/rest/v1/",
        oauth: bool = False,
        verify: typing.Union[bool, str, ssl.SSLContext] = True,
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
        self.__api_version = api_version
        self.__host_name = host + self.__api_version
        self.__credentials = credentials
        self.__oauth = oauth
        self.__verify = verify
        self.__session = self.session_class(verify=verify, timeout=timeout)

        # Setup OAuth if needed.
        if self.__oauth:
            self.__token_host = host + "/rest/oauth/token"
            self.__token = None
            self.__get_fresh_token()

    def get_available_endpoints(self):
        try:
            response = self.__session.get("")
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def close(self) -> None:
        """Method to close underlying session"""
        self.__session.close()

    def delete(self, resource: str, **kwargs):
        """This method will perform a delete operation on the specified
        resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.delete(url, **kwargs)

        return self.__session.delete(url, auth=self.__credentials, **kwargs)

    def get(self, resource: str, params: dict = None, **kwargs):
        """This method will perform a get operation on the specified
        resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.get(url, params=params, **kwargs)

        return self.__session.get(url, auth=self.__credentials, params=params, **kwargs)

    def patch(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a patch operation to the specified
        resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.patch(
                url, params=params, data=data, json=json, **kwargs
            )

        return self.__session.patch(
            url, auth=self.__credentials, params=params, data=data, json=json, **kwargs
        )

    def post(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a post operation to the specified
        resource."""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.post(
                url, params=params, data=data, json=json, **kwargs
            )

        return self.__session.post(
            url, auth=self.__credentials, params=params, data=data, json=json, **kwargs
        )

    def put(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a put operation to the specified
        resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.put(
                url, data=data, params=params, json=json, **kwargs
            )

        return self.__session.put(
            url, auth=self.__credentials, data=data, params=params, json=json, **kwargs
        )

    def __check_oauth_token(self):
        if self.__token is None:
            self._get_fresh_token()

        else:
            time_elapsed = time.time() - self.__token_acquired_at
            time_remaining = self.__token_expires_in - time_elapsed
            if time_remaining < 60:
                # if less than a minute remains, just get another token.
                self.__get_fresh_token()

    def __get_fresh_token(self):
        """This method will fetch a new oauth bearer token from the oauth
        token server."""
        data = {"grant_type": "client_credentials"}

        # By getting the system time before we get the token we avoid a
        # potential bug where the token may be expired.
        time_before_request = time.time()

        # Post to the token server, check if authorized
        try:
            response = httpx.post(
                self.__token_host,
                auth=self.__credentials,
                data=data,
                verify=self.__verify,
            )
            response.raise_for_status()
        except httpx.HTTPError as err:
            raise UnauthorizedTokenException(f"Unable to fetch token: {err}")

        # If success get relevant data
        if response.status_code in [200, 201]:
            response_json = response.json()
            self.__token = response_json["access_token"]
            self.__token_expires_in = response_json["expires_in"]
            self.__token_acquired_at = math.floor(time_before_request)

        else:
            py_jama_client_logger.error("Failed to retrieve OAuth Token")

    def __add_auth_header(self, **kwargs):
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["Authorization"] = "Bearer " + self.__token
        return headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.__session.close()

    def get_all(
        self,
        resource,
        params: Optional[dict] = None,
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
        allowed_results_per_page = 20
        total_results = float("inf")

        data, meta, links, linked = [], {}, {}, {}
        while len(data) < total_results:
            page = self.get_page(resource, start_index, params=params, **kwargs)

            meta.update(page.meta)
            links.update(page.links)

            for item_type_key in page.linked:
                if item_type_key not in linked:
                    linked[item_type_key] = {}
                linked[item_type_key] = {
                    **linked[item_type_key],
                    **page.linked[item_type_key],
                }

            page_info = page.meta.get("pageInfo")
            start_index = page_info.get("startIndex") + allowed_results_per_page
            total_results = page_info.get("totalResults")
            data.extend(page.data)

        return ClientResponse(meta, links, linked, data)

    def get_page(
        self,
        resource,
        start_at,
        params: dict = None,
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
                "API Client Error. Status: {} Message: {}".format(
                    status, response_message
                )
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
                    "API response message {}".format(response_message),
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
                )

            raise APIClientException(
                "{} {} Client Error.  Bad Request.  API response message: {}".format(
                    status, response.reason, response_message
                ),
                status_code=status,
                reason=response_message,
            )

        if status in range(500, 600):
            """These are server errors and network errors."""

            # Log The Error
            py_jama_client_logger.error(
                "{} Server error. {}".format(status, response.reason)
            )
            raise APIServerException(
                "{} Server Error.".format(status),
                status_code=status,
                reason=response.reason,
            )

        # Catch anything unexpected
        py_jama_client_logger.error("{} error. {}".format(status, response.reason))
        raise APIException(
            "{} error".format(status), status_code=status, reason=response.reason
        )
