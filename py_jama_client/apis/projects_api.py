"""
Projects API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> projects_api = ProjectsAPI(client)
    >>> projects = projects_api.get_projects()
"""

import json
import logging
from typing import Optional

from py_jama_client.client import ClientResponse, JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

py_jama_client_logger = logging.getLogger("py_jama_client")


class ProjectsAPI:
    client: JamaClient

    resource_path = "projects/"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_projects(
        self,
        params: Optional[dict] = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
    ):
        """
        This method will return all projects as JSON object
        optional: if project_id is specified, it will return a single project
        Args:
            allowed_results_per_page: number of results per page
        Returns:
            JSON Array of Item Objects.
        """
        resource_path = "projects"

        return self.client.get_all(
            resource_path, params, allowed_results_per_page=allowed_results_per_page
        )

    def get_project_by_id(self, project_id: int, params: Optional[dict] = None):
        """
        This method will return a single project as JSON object
        Args:
            project_id: the id of the project to fetch

        Returns: a dictionary object representing the project

        """
        resource_path = f"projects/{project_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise ResourceNotFoundException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_relationship_rule_set_projects(self, id: int):
        """
        This method will return the projects that have a given relationship
        rule set defined.

        Returns: An array of the dictionary objects representing the projects
        with a given rule set assigned

        """
        resource_path = f"relationshiprulesets/{id}/projects"
        return self.client.get_all(resource_path)

    def post_project_attachment(
        self,
        project_id: int,
        name: str,
        description: str,
        *args,
        params: Optional[dict] = None,
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

        resource_path = f"projects/{project_id}/attachments"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.post(
                resource_path,
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

    def put_project_item_type(
        self,
        project_id: int,
        item_type_id: int,
        *args,
        params: Optional[dict] = None,
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
        resource_path = f"projects/{project_id}/itemtypes/{item_type_id}"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(resource_path, params, headers=headers, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code
