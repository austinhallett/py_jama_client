"""
Test Runs API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> test_runs_api = TestRunsAPI(client)
    >>> test_runs = test_runs_api.get_test_runs()
"""

import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class TestRunsAPI:
    client: JamaClient

    resource_path = "testruns"

    def __init__(self, client: JamaClient):
        self.client = client

    def put_test_run(
        self,
        test_run_id: int,
        data: dict = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """This method will post a test run to Jama through the API"""
        resource_path = f"testruns/{test_run_id}"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path,
                params,
                data=data,
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code
