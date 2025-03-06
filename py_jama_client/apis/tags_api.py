"""
Tags API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> tags_api = TagsAPI(client)
    >>> tags = tags_api.get_tags()
"""

import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class TagsAPI:
    client: JamaClient

    resource_path = "tags"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_tags(
        self,
        project_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all tags for the project with the specified id
        Args:
            project: The API ID of the project to fetch tags for.
            allowed_results_per_page: Number of results per page

        Returns: A Json Array that contains all the tag data for the specified
        project.

        """
        req_params = {"project": project_id}
        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_tag(
        self,
        name: str,
        project: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Create a new tag in the project with the specified project ID
        Args:
            name: The display name for the tag
            project: The project to create the new tag in

        Returns: the newly created Tag
        """
        body = {"name": name, "project": project}
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

    def get_tag(
        self,
        tag_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets item tag information for a specific item tag id.
        Args:
            item_tag_id: The api id of the item tag to fetch

        Returns: JSON object
        """
        resource_path = f"tags/{tag_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_tag(
        self,
        tag_id: int,
        name: str,
        project: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Update an existing tag with the specified tag ID in the project with
        the specified project ID
        Args:
            tag_id: integer API id of the tag
            name: string name of the tag
            project: the project in which to update the tag
        """
        body = {"name": name, "project": project}
        resource_path = "tags/{}".format(tag_id)
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path, params, data=json.dumps(body), headers=headers, **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def delete_tag(self, tag_id: int) -> int:
        """
        Deletes a tag with the specified tag ID
        Args:
            tag_id: the api id of a tag

        Returns: The success status code.
        """
        resource_path = f"tags/{tag_id}"
        try:
            response = self.client.delete(resource_path)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_tag_items(
        self,
        tag_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all items that have the tag with the specified id
        Args:
            allowed_results_per_page: Number of results per page

        Returns: A Json Array containing all items tagged with the specified
        tag id.
        """
        resource_path = f"tags/{tag_id}/items"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )
