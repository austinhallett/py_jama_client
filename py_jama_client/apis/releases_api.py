"""
Releases API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> releases_api = releasesAPI(client)
    >>> releases = releases_api.get_releases(project_id=82)
"""

import datetime
import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class ReleasesAPI:
    client: JamaClient

    resource_path = "releases"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_releases(
        self,
        project_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all releases in the project with the specified ID

        Args:
            project_id: the api project id of a project
            allowed_results_per_page: number of results per page

        Returns: the client response

        docs: https://rest.jamasoftware.com/#operation_getReleases
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
        )

    def get_release(
        self,
        release_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the release with the specified ID

        Args:
            release_id: the api release id of a release

        Returns: the client response

        docs: https://rest.jamasoftware.com/#operation_getRelease
        """
        resource_path = f"releases/{release_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err)) from err
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_release(
        self,
        name: str,
        release_date: datetime.datetime,
        project_id: int,
        description: str = "",
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Create a new release

        Args:
            name: name of the release
            release_date: the date of the release
            project_id: the api project id of a project
            description: Optional description of the release

        Returns: the client response

        docs: https://rest.jamasoftware.com/#operation_addRelease
        """
        body = {
            "name": name,
            "description": description,
            "releaseDate": self.date_to_str(release_date),
            "project": project_id,
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
            raise APIException(str(err)) from err
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_release(
        self,
        release_id: int,
        name: str,
        release_date: datetime.datetime,
        project_id: int,
        description: str = "",
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Update the release with the specified ID

        Args:
            release_id: the api release id of the release
            name: name of the release
            release_date: the date of the release
            project_id: the api project id of a project
            description: Optional description of the release

        Returns: the client response

        docs: https://rest.jamasoftware.com/#operation_putRelease
        """
        body = {
            "name": name,
            "description": description,
            "releaseDate": self.date_to_str(release_date),
            "project": project_id,
        }
        resource_path = f"{self.resource_path}/{release_id}"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path, params, data=json.dumps(body), headers=headers, **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err)) from err
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def date_to_str(self, date: datetime.datetime) -> str:
        """format a date in the jama format"""

        return date.strftime("%Y-%m-%d")
