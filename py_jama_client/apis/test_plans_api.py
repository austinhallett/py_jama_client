"""
Test Plans API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> test_plans_api = TestPlansAPI(client)
    >>> test_plans = test_plans_api.get_test_plans()
"""

import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class TestPlansAPI:
    client: JamaClient

    resource_path = "testplans"

    def __init__(self, client: JamaClient):
        self.client = client

    def post_testplans_testcycles(
        self,
        testplan_id: int,
        testcycle_name: str,
        start_date: str,
        end_date: str,
        testgroups_to_include: list[int] = None,
        testrun_status_to_include: list[str] = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will create a new Test Cycle.

        Args:
            testplan_id (int): The API_ID of the testplan to create the test
                cycle from.
            testcycle_name (str): The name you would like to set for the new
                Test Cycle
            start_date (str): Start date in 'yyyy-mm-dd' Format
            end_date (str): End date in 'yyyy-mm-dd' Format
            testgroups_to_include (int[]):  This array of integers specify the
                test groups to be included.
            testrun_status_to_include (str[]): Only valid after generating the
                first Test Cycle, you may choose to only generate Test Runs
                that were a specified status in the previous cycle. Do not
                specify anything to include all statuses

        Returns:
            (int): Returns the the newly created testcycle
        """
        resource_path = f"testplans/{testplan_id}/testcycles"
        headers = {"content-type": "application/json"}
        fields = {"name": testcycle_name, "startDate": start_date, "endDate": end_date}
        test_run_gen_config = {}
        if testgroups_to_include is not None:
            test_run_gen_config["testGroupsToInclude"] = testgroups_to_include
        if testrun_status_to_include is not None:
            test_run_gen_config["testRunStatusesToInclude"] = testrun_status_to_include
        body = {"fields": fields, "testRunGenerationConfig": test_run_gen_config}

        # Make the API Call
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

        # Validate response
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
