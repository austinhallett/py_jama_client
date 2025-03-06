"""
Filters API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> filters_api = FiltersAPI(client)
    >>> filters = filters_api.get_filter_results()
"""

import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_client_logger = logging.getLogger("py_jama_client")


class FiltersAPI:
    client: JamaClient

    resource_path = "testruns"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_filter_results(
        self,
        filter_id: int,
        project_id: int = None,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all results items for the filter with the specified ID

        Args:
            filter_id: The ID of the filter to fetch the results for.
            project_id: Use this only for filters that run on any project,
                where projectScope is CURRENT
            allowed_results_per_page: Number of results per page

        Returns:
            A List of items that match the filter.

        """
        resource_path = f"filters/{filter_id}/results"

        req_params = {"project": project_id}

        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )
