"""
Tags API module

Example usage:

    >>> from py_jama_rest_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> tags_api = TagsAPI(client)
    >>> tags = tags_api.get_tags()    
"""

import json
import logging
from typing import Optional
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.client import JamaClient
from py_jama_client.response import ClientResponse
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_client_logger = logging.getLogger("py_jama_rest_client")


class TagsAPI:
    client: JamaClient

    resource_path = "tags"

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

        Returns: A Json Array that contains all the tag data for the specified project.

        """
        req_params = {"project": project_id}
        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.get_all(
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
        Create a new tag in the project with the specified ID
        Args:
            name: The display name for the tag
            project: The project to create the new tag in

        Returns: the newly created Tag
        """
        body = {"name": name, "project": project}
        headers = {"content-type": "application/json"}
        try:
            response = self._core.post(
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
