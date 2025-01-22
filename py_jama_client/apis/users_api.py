"""
User API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> users_api = UsersAPI(client)
    >>> users = users_api.get_users()
"""

import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class UsersAPI:
    client: JamaClient

    resource_path = "users"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_users(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Gets a list of all active users visible to the current user

        Args:
            allowed_results_per_page: Number of results per page

        Returns: JSON array

        """
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_user(
        self,
        user_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets a single speificed user

        Args:
            user_id: user api ID

        Returns: JSON obect

        """
        resource_path = f"{self.resource_path}/{user_id}"
        try:
            response = self.client.get(
                resource_path,
                params,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        return ClientResponse.from_response(response)

    def get_current_user(
        self,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets a current user

        Returns: JSON obect

        """
        resource_path = f"{self.resource_path}/current"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        return ClientResponse.from_response(response)

    def get_current_user_favorite_filters(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Gets a list of favorite filters for the current user

        Args:
            allowed_results_per_page: Number of results per page

        Returns: JSON array

        """
        resource_path = f"{self.resource_path}/current/favoritefilters"

        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_user(
        self,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        email: str,
        license_type: str,
        phone: str = None,
        title: str = None,
        location: str = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Creates a new user

        Args:
            username: str
            password: str
            first_name: str
            last_name: str
            email: str
            phone: str - optional
            title: str - optional
            location: str - optional
            licenseType: enum [ NAMED, FLOATING, STAKEHOLDER,
                                FLOATING_COLLABORATOR,
                                RESERVED_COLLABORATOR, FLOATING_REVIEWER,
                                RESERVED_REVIEWER, NAMED_REVIEWER,
                                TEST_RUNNER, EXPIRING_TRIAL, INACTIVE ]

        Returns: newly created user

        """

        body = {
            "username": username,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "title": title,
            "location": location,
            "licenseType": license_type,
        }
        headers = {"content-type": "application/json"}
        try:
            response = self.client.post(
                self.resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_user(
        self,
        user_id: int,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str = None,
        title: str = None,
        location: str = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        updates an existing user

        Args:
            username: str
            password: str
            first_name: str
            last_name: str
            email: str
            phone: str - optional
            title: str - optional
            location: str - optional

        Returns: api status code

        """

        body = {
            "username": username,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "title": title,
            "location": location,
        }
        resource_path = f"{self.resource_path}/{user_id}"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        self.handle_response_status(response)
        return response.status_code

    def put_user_active(
        self,
        user_id: int,
        is_active: bool,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        updates an existing users active status

        Args:
            is_active: boolean

        Returns: api status code

        """
        body = {"active": is_active}
        resource_path = f"{self.resource_path}/{user_id}/active"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        self.handle_response_status(response)
        return response.status_code
