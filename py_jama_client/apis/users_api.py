"""
User API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> users_api = UsersAPI(client)
    >>> users = users_api.get_users()
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
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
        *,
        params: dict | None = None,
        username: str | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        license_type: str | None = None,
        include_inactive: bool | None = None,
        project: int | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Gets a list of all active users visible to the current user

        Args:
            include: links to include as full objects in the linked map
            username: only users with this username (sent as username)
            email: only users with this email (sent as email)
            first_name: only users with this first name (sent as firstName)
            last_name: only users with this last name (sent as lastName)
            license_type: only users with this license type, e.g. NAMED
                (sent as licenseType)
            include_inactive: also return inactive users (sent as
                includeInactive)
            project: only users of the project with this API ID (sent as
                project)
            Each of these overrides the same key in params.
            allowed_results_per_page: Number of results per page

        Returns: JSON array

        """
        params = with_include(params, include)
        params = with_query(
            params,
            username=username,
            email=email,
            firstName=first_name,
            lastName=last_name,
            licenseType=license_type,
            includeInactive=include_inactive,
            project=project,
        )
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_user(
        self,
        user_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Gets a single speificed user

        Args:
            include: links to include as full objects in the linked map
            user_id: user api ID

        Returns: JSON obect

        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(user_id)}"
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Gets a current user

        Returns: JSON obect

        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/current"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        return ClientResponse.from_response(response)

    def get_current_user_favorite_filters(
        self,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Gets a list of favorite filters for the current user

        Args:
            include: links to include as full objects in the linked map
            allowed_results_per_page: Number of results per page

        Returns: JSON array

        """
        params = with_include(params, include)
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
        phone: str | None = None,
        title: str | None = None,
        location: str | None = None,
        *,
        params: dict | None = None,
        authentication_type: dict | None = None,
        custom_data: list[dict] | None = None,
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
            authentication_type: dict with the authentication type's id and
                name, e.g. {"id": 1, "name": "LDAP"}; left out when None
            custom_data: list of {"name": ..., "value": ...} dicts; left out
                when None

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
        if authentication_type is not None:
            body["authenticationType"] = authentication_type
        if custom_data is not None:
            body["customData"] = custom_data
        try:
            response = self.client.post(
                self.resource_path,
                params,
                json=body,
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
        phone: str | None = None,
        title: str | None = None,
        location: str | None = None,
        *,
        params: dict | None = None,
        authentication_type: dict | None = None,
        custom_data: list[dict] | None = None,
        license_type: str | None = None,
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
            authentication_type: dict with the authentication type's id and
                name, e.g. {"id": 1, "name": "LDAP"}; left out when None
            custom_data: list of {"name": ..., "value": ...} dicts; left out
                when None
            license_type: the user's license type (same values as for
                post_user); left out when None

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
        if authentication_type is not None:
            body["authenticationType"] = authentication_type
        if custom_data is not None:
            body["customData"] = custom_data
        if license_type is not None:
            body["licenseType"] = license_type
        resource_path = f"{self.resource_path}/{segment(user_id)}"
        try:
            response = self.client.put(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def put_user_active(
        self,
        user_id: int,
        is_active: bool,
        *,
        params: dict | None = None,
        **kwargs,
    ):
        """
        updates an existing users active status

        Args:
            is_active: boolean

        Returns: api status code

        """
        body = {"active": is_active}
        resource_path = f"{self.resource_path}/{segment(user_id)}/active"
        try:
            response = self.client.put(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_user_custom_data(
        self,
        user_id: int,
        *,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the custom data of a user. Admin operation; implemented from the
        REST docs and not exercised against a live instance. The docs list no
        startAt/maxResults for this endpoint, but its response carries
        pageInfo, so it is paged like the other list reads.

        Args:
            user_id: The API ID of the user
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is a list of
            {"name": ..., "value": ...} entries
        """
        return self.client.get_all(
            f"users/{segment(user_id)}/customData",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def put_user_custom_data(
        self,
        user_id: int,
        custom_data: list[dict],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update the custom data of a user. Admin operation; implemented from
        the REST docs and not exercised against a live instance.

        Args:
            user_id: The API ID of the user
            custom_data: The request body, a list of {"name": ..., "value": ...}
            params: optional query parameters

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"users/{segment(user_id)}/customData",
            params,
            json=custom_data,
            **kwargs,
        ).status_code

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
