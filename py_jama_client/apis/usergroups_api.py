"""
User Groups API module

Admin operations; implemented from the REST docs and not exercised against a
live instance.

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> user_groups_api = UserGroupsAPI(client)
    >>> user_groups = user_groups_api.get_user_groups().data
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class UserGroupsAPI:
    client: JamaClient

    resource_path = "usergroups"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_user_groups(
        self,
        *,
        params: dict | None = None,
        project: int | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all user groups

        Args:
            include: links to include as full objects in the linked map
            params: optional query parameters
            project: only user groups of the project with this API ID (sent as
                project; overrides the same key in params)
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of user groups
        """
        params = with_include(params, include)
        params = with_query(params, project=project)
        return self.client.get_all(
            self.resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_user_group(
        self,
        name: str,
        description: str,
        project: int | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a user group

        Args:
            name: The group name
            description: The group description
            project: The API ID of the project the group belongs to; left out
                of the request when None
            params: optional query parameters

        Returns: the client response; the new group ID is in meta.id
        """
        return ClientResponse.from_response(
            self._call(
                self.client.post,
                self.resource_path,
                params,
                json=self._group_body(name, description, project),
                **kwargs,
            )
        )

    def get_user_group(
        self,
        user_group_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Get a user group

        Args:
            include: links to include as full objects in the linked map
            user_group_id: The API ID of the user group
            params: optional query parameters, e.g. include

        Returns: the client response, whose data is the user group
        """
        params = with_include(params, include)
        return ClientResponse.from_response(
            self._call(
                self.client.get,
                f"usergroups/{segment(user_group_id)}",
                params,
                **kwargs,
            )
        )

    def put_user_group(
        self,
        user_group_id: int,
        name: str,
        description: str,
        project: int | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a user group. PUT replaces the group. When project is None the
        key is left out of the body; what the server does with an omitted
        project is undocumented and unverified (admin operation, never run
        live).

        Args:
            user_group_id: The API ID of the user group
            name: The group name
            description: The group description
            project: The API ID of the project the group belongs to; left out
                of the request when None
            params: optional query parameters

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"usergroups/{segment(user_group_id)}",
            params,
            json=self._group_body(name, description, project),
            **kwargs,
        ).status_code

    def delete_user_group(self, user_group_id: int, **kwargs) -> int:
        """
        Delete a user group

        Args:
            user_group_id: The API ID of the user group

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete, f"usergroups/{segment(user_group_id)}", **kwargs
        ).status_code

    def get_user_group_users(
        self,
        user_group_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the users in a user group

        Args:
            include: links to include as full objects in the linked map
            user_group_id: The API ID of the user group
            params: optional query parameters, e.g. include
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of users
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"usergroups/{segment(user_group_id)}/users",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_user_group_user(
        self,
        user_group_id: int,
        user_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add an existing user to a user group

        Args:
            user_group_id: The API ID of the user group
            user_id: The API ID of the user
            params: optional query parameters

        Returns: the client response
        """
        return ClientResponse.from_response(
            self._call(
                self.client.post,
                f"usergroups/{segment(user_group_id)}/users",
                params,
                json={"user": user_id},
                **kwargs,
            )
        )

    def delete_user_group_user(self, user_group_id: int, user_id: int, **kwargs) -> int:
        """
        Remove a user from a user group

        Args:
            user_group_id: The API ID of the user group
            user_id: The API ID of the user

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete,
            f"usergroups/{segment(user_group_id)}/users/{segment(user_id)}",
            **kwargs,
        ).status_code

    @staticmethod
    def _group_body(name: str, description: str, project: int | None) -> dict:
        body: dict = {"name": name, "description": description}
        if project is not None:
            body["project"] = project
        return body

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
