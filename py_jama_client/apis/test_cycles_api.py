"""
Test Cycles API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> test_cycles_api = TestCyclesAPI(client)
    >>> test_cycles = test_cycles_api.get_test_cycles()
"""

import logging

from py_jama_client.apis._include import with_include
from py_jama_client.apis._path import segment
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        This method will return JSON data about the test cycle specified by
        the test cycle id.

        Args:
            include: links to include as full objects in the linked map
            test_cycle_id: the api id of the test cycle to fetch

        Returns: a dictionary object that represents the test cycle

        """
        params = with_include(params, include)
        resource_path = f"testcycles/{segment(test_cycle_id)}"
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all test runs associated with the specified
        test cycle.  Test runs will be returned as a list of json objects.
        Args:
            include: links to include as full objects in the linked map
            test_cycle_id: (int) The id of the test cycle
        """
        params = with_include(params, include)
        resource_path = f"testcycles/{segment(test_cycle_id)}/testruns"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_cycle_test_group(
        self,
        test_cycle_id: int,
        test_group_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a test group of a test cycle

        Args:
            include: links to include as full objects in the linked map
            test_cycle_id: The API ID of the test cycle
            test_group_id: The API ID of the test group
            params: optional query parameters

        Returns: the client response, whose data is the test group
        """
        params = with_include(params, include)
        return self._get(
            f"testcycles/{segment(test_cycle_id)}/testgroup/{segment(test_group_id)}",
            params,
            **kwargs,
        )

    def get_test_cycle_versions(
        self,
        test_cycle_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all versions of a test cycle

        Args:
            include: links to include as full objects in the linked map
            test_cycle_id: The API ID of the test cycle
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of versions
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testcycles/{segment(test_cycle_id)}/versions",
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_cycle_version(
        self,
        test_cycle_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get one version of a test cycle

        Args:
            include: links to include as full objects in the linked map
            test_cycle_id: The API ID of the test cycle
            version_num: The version number
            params: optional query parameters

        Returns: the client response, whose data is the version
        """
        params = with_include(params, include)
        return self._get(
            f"testcycles/{segment(test_cycle_id)}/versions/{segment(version_num)}",
            params,
            **kwargs,
        )

    def get_test_cycle_versioned_item(
        self,
        test_cycle_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the test cycle as it was at a version

        Args:
            include: links to include as full objects in the linked map
            test_cycle_id: The API ID of the test cycle
            version_num: The version number
            params: optional query parameters

        Returns: the client response, whose data is the test cycle at that version
        """
        params = with_include(params, include)
        return self._get(
            f"testcycles/{segment(test_cycle_id)}/versions/{segment(version_num)}/versioneditem",
            params,
            **kwargs,
        )

    def delete_test_cycle(self, test_cycle_id: int, **kwargs) -> int:
        """
        Delete a test cycle and its test runs

        Args:
            test_cycle_id: The API ID of the test cycle

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete, f"testcycles/{segment(test_cycle_id)}", **kwargs
        ).status_code

    def patch_test_cycle(
        self,
        test_cycle_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Patch a test cycle.

        Args:
            test_cycle_id: The API ID of the test cycle
            patches: Patch operations, each with op, path and a value where the op
                needs one (remove takes none), e.g.
                {"op": "replace", "path": "/fields/name", "value": "New name"}.

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.patch,
            f"testcycles/{segment(test_cycle_id)}",
            params,
            json=patches,
            **kwargs,
        ).status_code

    def put_test_cycle(
        self,
        test_cycle_id: int,
        fields: dict,
        *,
        params: dict | None = None,
        test_run_generation_config: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a test cycle. PUT replaces all fields: name, startDate and
        endDate are required, and leaving one out raises APIClientException
        (400) with the cycle left unchanged. Use patch_test_cycle for partial
        updates.

        Args:
            test_cycle_id: The API ID of the test cycle
            fields: Field names to values, e.g. {"name": "Cycle"}.
            test_run_generation_config: test run generation settings, e.g.
                {"testGroupsToInclude": [1, 2]}; omit testGroupsToInclude to
                include all test groups. Omitted from the request when None.

        Returns:
            (int): The response status code.
        """
        body: dict = {"fields": fields}
        if test_run_generation_config is not None:
            body["testRunGenerationConfig"] = test_run_generation_config
        return self._call(
            self.client.put,
            f"testcycles/{segment(test_cycle_id)}",
            params,
            json=body,
            **kwargs,
        ).status_code

    def _get(self, resource_path: str, params: dict | None, **kwargs) -> ClientResponse:
        return ClientResponse.from_response(
            self._call(self.client.get, resource_path, params, **kwargs)
        )

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
