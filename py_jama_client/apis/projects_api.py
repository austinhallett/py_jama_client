"""
Projects API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> projects_api = ProjectsAPI(client)
    >>> projects = projects_api.get_projects()
"""

import logging

import httpx

from py_jama_client.apis._include import with_include
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class ProjectsAPI:
    client: JamaClient

    resource_path = "projects/"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_projects(
        self,
        params: dict | None = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *,
        include: list[str] | None = None,
    ):
        """
        This method will return all projects as JSON object
        optional: if project_id is specified, it will return a single project
        Args:
            include: links to include as full objects in the linked map
            allowed_results_per_page: number of results per page
        Returns:
            JSON Array of Item Objects.
        """
        params = with_include(params, include)
        resource_path = "projects"

        return self.client.get_all(
            resource_path, params, allowed_results_per_page=allowed_results_per_page
        )

    def get_project_by_id(
        self,
        project_id: int,
        params: dict | None = None,
        *,
        include: list[str] | None = None,
    ):
        """
        This method will return a single project as JSON object
        Args:
            include: links to include as full objects in the linked map
            project_id: the id of the project to fetch

        Returns: a dictionary object representing the project

        """
        params = with_include(params, include)
        resource_path = f"projects/{segment(project_id)}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise ResourceNotFoundException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_types_in_project(
        self,
        project_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all item types enabled for a project

        Args:
            include: links to include as full objects in the linked map
            project_id: the id of the project
            params: optional query parameters, e.g. include
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of item types

        docs: https://rest.jamasoftware.com/#operation_getItemTypesInProject
        """
        params = with_include(params, include)
        resource_path = f"projects/{segment(project_id)}/itemtypes"
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_tags_in_project(
        self,
        project_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all tags in a project

        Reads projects/{id}/tags, whereas TagsAPI.get_tags reads tags?project=.

        Args:
            include: links to include as full objects in the linked map
            project_id: the id of the project
            params: optional query parameters, e.g. include
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of tags

        docs: https://rest.jamasoftware.com/#operation_getTagsInProject
        """
        params = with_include(params, include)
        resource_path = f"projects/{segment(project_id)}/tags"
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_relationship_rule_set_projects(self, id: int):
        """
        This method will return the projects that have a given relationship
        rule set defined.

        Returns: An array of the dictionary objects representing the projects
        with a given rule set assigned

        """
        resource_path = f"relationshiprulesets/{segment(id)}/projects"
        return self.client.get_all(resource_path)

    def post_project_attachment(
        self,
        project_id: int,
        name: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ):
        """
        This Method will make a new attachment object in the specified project
        :param project_id: The integer project ID to create the attachment in.
        :param name:  The name of the attachment
        :param description: The description of the attachment
        :return: Returns the ID of the newly created attachment object.
        """
        body = {"fields": {"name": name, "description": description}}

        resource_path = f"projects/{segment(project_id)}/attachments"
        try:
            response = self.client.post(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_project_item_type(
        self,
        project_id: int,
        item_type_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ):
        """
        Add item type to project
        Args:
            :param project_id: The integer project ID to add item type to.
            :param item_type_id integer ID of an Item Type.

        Returns:
            response status 200

        """
        resource_path = (
            f"projects/{segment(project_id)}/itemtypes/{segment(item_type_id)}"
        )
        headers = httpx.Headers({"content-type": "application/json"})
        headers.update(kwargs.pop("headers", None) or {})
        try:
            response = self.client.put(resource_path, params, headers=headers, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def post_project(
        self,
        project: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a project or project folder. Admin operation; implemented from
        the REST docs and not exercised against a live instance.

        Args:
            project: The request body. The documented fields are projectKey
                (not needed for a folder), isFolder, parent and fields (a map
                of project field names to values, e.g. {"name": "Example"}).
            params: optional query parameters

        Returns: the client response; the docs show only meta in the response
        """
        return ClientResponse.from_response(
            self._call(self.client.post, "projects", params, json=project, **kwargs)
        )

    def put_project(
        self,
        project_id: int,
        project: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a project. Admin operation; implemented from the REST docs and
        not exercised against a live instance.

        Args:
            project_id: The API ID of the project
            project: The request body; same fields as post_project
            params: optional query parameters

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"projects/{segment(project_id)}",
            params,
            json=project,
            **kwargs,
        ).status_code

    def delete_project_item_type(
        self, project_id: int, item_type_id: int, **kwargs
    ) -> int:
        """
        Remove an item type from a project. Admin operation; implemented from
        the REST docs and not exercised against a live instance.

        Args:
            project_id: The API ID of the project
            item_type_id: The API ID of the item type

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete,
            f"projects/{segment(project_id)}/itemtypes/{segment(item_type_id)}",
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
