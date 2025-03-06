"""
Test Cycles API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> test_cycles_api = TestCyclesAPI(client)
    >>> test_cycles = test_cycles_api.get_test_cycles()
"""

import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class TestCyclesAPI:
    client: JamaClient

    resource_path = "testcycles"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_test_cycle(
        self,
        test_cycle_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return JSON data about the test cycle specified by
        the test cycle id.

        Args:
            test_cycle_id: the api id of the test cycle to fetch

        Returns: a dictionary object that represents the test cycle

        """
        resource_path = f"testcycles/{test_cycle_id}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_test_cycle_runs(
        self,
        test_cycle_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all test runs associated with the specified
        test cycle.  Test runs will be returned as a list of json objects.
        Args:
            test_cycle_id: (int) The id of the test cycle
        """
        resource_path = f"testcycles/{test_cycle_id}/testruns"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )
