"""
Baseline API module

Example usage:

    >>> from py_jama_rest_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> baselines_api = BaselinesAPI(client)
    >>> baselines = baselines_api.get_baselines()    
"""

import logging
from typing import Optional
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.client import JamaClient
from py_jama_client.response import ClientResponse
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_rest_client_logger = logging.getLogger("py_jama_rest_client")


class BaselinesAPI:
    client: JamaClient

    resource_path = "baselines"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_baselines(
        self,
        project_id: int,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
    ) -> ClientResponse:
        """
        Returns a list of Baseline objects
        Args:
            project_id:  the Id of the project to fetch baselines for
            allowed_results_per_page: number of results per page

        Returns: a list of Baseline objects
        """
        resource_path = "baselines"
        if params is not None:
            params.update({"project": project_id})
        else:
            params = {"project": project_id}

        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_baseline(
        self,
        baseline_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get baseline by id

        Args:
            baseline_id: the id of the baseline to fetch

        Returns:
            a dictionary object representing the baseline

        """
        resource_path = "baselines/" + str(baseline_id)

        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_baselines_versioneditems(
        self,
        baseline_id: int,
        params: Optional[dict] = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
    ):
        """
        Get all baseline items in a baseline with the specified ID
        Args:
            baseline_id:  The id of the baseline to fetch items for.
            allowed_results_per_page: Number of results per page
        Returns: A list of versioned items belonging to the baseline
        """
        resource_path = "baselines/" + str(baseline_id) + "/versioneditems"
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )
