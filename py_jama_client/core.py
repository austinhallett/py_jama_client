"""
Core Jama Connect API class

This module contains core classes for interacting with the Jama Connect API

Classes:
    Core: This is the base class
    AsyncCore: This class inherits the Core class using the httpx.AsyncClient class
"""

import math
import urllib3
import httpx
import time
import logging
from py_jama_client.exceptions import UnauthorizedTokenException
from typing import Tuple
from abc import ABC, abstractmethod


class AbstractCore(ABC):
    """
    Abstract core class
    This class defines the interface required to satisfy the base requirements of the client core class
    """

    @abstractmethod
    def close(self) -> None:
        """
        Method to close underlying session
        """
        ...

    @abstractmethod
    def delete(self, resource: str, **kwargs):
        """
        This method will perform a delete operation on the specified resource
        """
        ...

    @abstractmethod
    def get(self, resource: str, params: dict = None, **kwargs):
        """
        This method will perform a get operation on the specified resource
        """
        ...

    @abstractmethod
    def patch(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """
        This method will perform a patch operation to the specified resource
        """
        ...

    @abstractmethod
    def post(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """
        This method will perform a post operation to the specified resource.
        """
        ...

    @abstractmethod
    def put(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """
        This method will perform a put operation to the specified resource
        """
        ...

    @abstractmethod
    def _check_oauth_token(self):
        ...

    @abstractmethod
    def _get_fresh_token(self):
        """
        This method will fetch a new oauth bearer token from the oauth token server.
        """
        ...

    @abstractmethod
    def _add_auth_header(self, **kwargs):
        ...


__DEBUG__ = False

py_jama_rest_client_logger = logging.getLogger("py_jama_client.core")

# disable warnings for ssl verification
urllib3.disable_warnings()


class Core(AbstractCore):
    """
    Synchronous Core API client class

    This class provides the basic http abstractions, including oauth related mechanisms.
    Use an instance of this class as an argument in the JamaClient constructor.
    """

    session_class = httpx.Client

    def __init__(
        self,
        host: str,
        credentials: Tuple[str, str] = ("username|client_id", "password|client_secret"),
        api_version: str = "/rest/v1/",
        oauth: bool = False,
        verify: bool = True,
        timeout: int = 30,
    ):
        # Instance variables
        self.__api_version = api_version
        self.__host_name = host + self.__api_version
        self.__credentials = credentials
        self.__oauth = oauth
        self.__verify = verify
        self._session = self.session_class(verify=verify, timeout=timeout)

        # Setup OAuth if needed.
        if self.__oauth:
            self.__token_host = host + "/rest/oauth/token"
            self.__token = None
            self._get_fresh_token()

    def close(self) -> None:
        """Method to close underlying session"""
        self._session.close()

    async def close(self) -> None:
        raise RuntimeError("await syntax not supported on sync core client class")

    def delete(self, resource: str, **kwargs):
        """This method will perform a delete operation on the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.delete(url, **kwargs)

        return self._session.delete(url, auth=self.__credentials, **kwargs)

    def get(self, resource: str, params: dict = None, **kwargs):
        """This method will perform a get operation on the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.get(url, params=params, **kwargs)

        return self._session.get(url, auth=self.__credentials, params=params, **kwargs)

    def patch(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a patch operation to the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.patch(
                url, params=params, data=data, json=json, **kwargs
            )

        return self._session.patch(
            url, auth=self.__credentials, params=params, data=data, json=json, **kwargs
        )

    def post(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a post operation to the specified resource."""
        url = self.__host_name + resource

        if self.__oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.post(
                url, params=params, data=data, json=json, **kwargs
            )

        return self._session.post(
            url, auth=self.__credentials, params=params, data=data, json=json, **kwargs
        )

    def put(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a put operation to the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self._check_oauth_token()
            kwargs["headers"] = self._add_auth_header(**kwargs)
            return self._session.put(url, data=data, params=params, json=json, **kwargs)

        return self._session.put(
            url, auth=self.__credentials, data=data, params=params, json=json, **kwargs
        )

    def _check_oauth_token(self):
        if self.__token is None:
            self._get_fresh_token()

        else:
            time_elapsed = time.time() - self.__token_acquired_at
            time_remaining = self.__token_expires_in - time_elapsed
            if time_remaining < 60:
                # if less than a minute remains, just get another token.
                self.__get_fresh_token()

    def _get_fresh_token(self):
        """This method will fetch a new oauth bearer token from the oauth token server."""
        data = {"grant_type": "client_credentials"}

        # By getting the system time before we get the token we avoid a potential bug where the token may be expired.
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
            py_jama_rest_client_logger.error("Failed to retrieve OAuth Token")

    def _add_auth_header(self, **kwargs):
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["Authorization"] = "Bearer " + self.__token
        return headers


class AsyncCore(Core):
    session_class = httpx.AsyncClient

    async def close(self):
        return await self._session.aclose()
