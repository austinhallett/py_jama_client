"""
Test Runs API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> test_runs_api = TestRunsAPI(client)
    >>> test_runs = test_runs_api.get_test_runs(params={"testCycle": CYCLE_ID})
"""

import logging

import httpx

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
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

    def get_test_runs(
        self,
        *,
        params: dict | None = None,
        test_cycle: list[int] | None = None,
        test_case: list[int] | None = None,
        test_plan: list[int] | None = None,
        sort_by: list[str] | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Search for test runs. The API documents that at least one of
        test_cycle, test_case or test_plan (testCycle, testCase, testPlan) is
        required; without one the server returns an empty list.

        Args:
            include: links to include as full objects in the linked map
            params: optional query parameters, e.g. {"testCycle": 5}
            test_cycle: list of test cycle IDs; only test runs in these test
                cycles (sent as testCycle)
            test_case: list of test case IDs; only test runs from these test
                cases (sent as testCase)
            test_plan: list of test plan IDs; only test runs in these test
                plans (sent as testPlan)
            sort_by: Sort orders can be added with the name of the field by
                which to sort, followed by .asc or .desc (e.g. 'name.asc' or
                'testCycle.desc'). If not set, this defaults to documentKey.asc
                (sent as sortBy)
            Each of these overrides the same key in params.
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of test runs
        """
        params = with_include(params, include)
        params = with_query(
            params,
            testCycle=test_cycle,
            testCase=test_case,
            testPlan=test_plan,
            sortBy=sort_by,
        )
        return self._get_all("testruns", params, allowed_results_per_page, **kwargs)

    def get_test_run(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters

        Returns: the client response, whose data is the test run
        """
        params = with_include(params, include)
        return self._get(
            f"testruns/{segment(test_run_id)}",
            params,
            **kwargs,
        )

    def get_test_run_activities(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the activity stream of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of activities
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/activities",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_attachments(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the attachments of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of attachments
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/attachments",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_comments(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        root_comments_only: bool | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the comments on a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            root_comments_only: if True, get only root comments, without their
                replies (sent as rootCommentsOnly; overrides the same key in
                params)
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of comments
        """
        params = with_include(params, include)
        params = with_query(params, rootCommentsOnly=root_comments_only)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/comments",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_downstream_related(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the items downstream of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of items
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/downstreamrelated",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_downstream_relationships(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the downstream relationships of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of relationships
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/downstreamrelationships",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_upstream_related(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the items upstream of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of items
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/upstreamrelated",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_upstream_relationships(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the upstream relationships of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of relationships
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/upstreamrelationships",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_links(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the links on a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of links
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/links",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_tags(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the tags on a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of tags
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/tags",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_versions(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all versions of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of versions
        """
        params = with_include(params, include)
        return self._get_all(
            f"testruns/{segment(test_run_id)}/versions",
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_test_run_link(
        self,
        test_run_id: int,
        link_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a link on a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            link_id: The ID of the link
            params: optional query parameters

        Returns: the client response, whose data is the link
        """
        params = with_include(params, include)
        return self._get(
            f"testruns/{segment(test_run_id)}/links/{segment(link_id)}",
            params,
            **kwargs,
        )

    def get_test_run_lock(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the locked state, last locked date and last locked by user of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            params: optional query parameters

        Returns: the client response, whose data is the lock information
        """
        params = with_include(params, include)
        return self._get(
            f"testruns/{segment(test_run_id)}/lock",
            params,
            **kwargs,
        )

    def get_test_run_tag(
        self,
        test_run_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a tag on a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            tag_id: The API ID of the tag on the test run
            params: optional query parameters

        Returns: the client response, whose data is the tag
        """
        params = with_include(params, include)
        return self._get(
            f"testruns/{segment(test_run_id)}/tags/{segment(tag_id)}",
            params,
            **kwargs,
        )

    def get_test_run_version(
        self,
        test_run_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get one version of a test run

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            version_num: The version number
            params: optional query parameters

        Returns: the client response, whose data is the version
        """
        params = with_include(params, include)
        return self._get(
            f"testruns/{segment(test_run_id)}/versions/{segment(version_num)}",
            params,
            **kwargs,
        )

    def get_test_run_versioned_item(
        self,
        test_run_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the test run as it was at a version

        Args:
            include: links to include as full objects in the linked map
            test_run_id: The API ID of the test run
            version_num: The version number
            params: optional query parameters

        Returns: the client response, whose data is the test run at that version
        """
        params = with_include(params, include)
        return self._get(
            f"testruns/{segment(test_run_id)}/versions/{segment(version_num)}/versioneditem",
            params,
            **kwargs,
        )

    def patch_test_run(
        self,
        test_run_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Patch a test run.

        Args:
            test_run_id: The API ID of the test run
            patches: Patch operations, each with op, path and value,
                e.g. {"op": "replace", "path": "/fields/testRunStatus",
                "value": "PASSED"}.

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.patch,
            f"testruns/{segment(test_run_id)}",
            params,
            json=patches,
            **kwargs,
        ).status_code

    def delete_test_run(self, test_run_id: int, **kwargs) -> int:
        """
        Delete a test run

        Args:
            test_run_id: The API ID of the test run

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete, f"testruns/{segment(test_run_id)}", **kwargs
        ).status_code

    def put_test_run(
        self,
        test_run_id: int,
        data: dict | str | bytes | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update the execution results of a test run. PUT changes only the
        fields passed; omitted fields keep their values, and fields the
        server treats as read-only (such as name) are ignored with a 200.

        Args:
            test_run_id: The API ID of the test run
            data: The request body, e.g. {"fields": {"actualResults": "Text"}}.
                Required; the server answers 400 when "fields" is missing.

        Returns:
            (int): The response status code.
        """
        if data is None:
            raise ValueError("data (the request body with 'fields') is required")
        if isinstance(data, (str, bytes)):
            kwargs["content"] = data
            headers = httpx.Headers({"content-type": "application/json"})
            headers.update(kwargs.get("headers") or {})
            kwargs["headers"] = headers
        else:
            kwargs["json"] = data
        return self._call(
            self.client.put, f"testruns/{segment(test_run_id)}", params, **kwargs
        ).status_code

    def post_test_run_link(
        self,
        test_run_id: int,
        url: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add a URL link to a test run.

        Args:
            test_run_id: The API ID of the test run
            url: The URL to link to
            description: The link text

        Returns: the client response; the new link ID is in meta.id
        """
        body = {"url": url, "description": description}
        return self._post(
            f"testruns/{segment(test_run_id)}/links", body, params, **kwargs
        )

    def put_test_run_link(
        self,
        test_run_id: int,
        link_id: int,
        url: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a URL link on a test run.

        Args:
            test_run_id: The API ID of the test run
            link_id: The ID of the link
            url: The URL to link to
            description: The link text

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"testruns/{segment(test_run_id)}/links/{segment(link_id)}",
            params,
            json={"url": url, "description": description},
            **kwargs,
        ).status_code

    def delete_test_run_link(self, test_run_id: int, link_id: int, **kwargs) -> int:
        """
        Remove a link from a test run.

        Args:
            test_run_id: The API ID of the test run
            link_id: The ID of the link

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete,
            f"testruns/{segment(test_run_id)}/links/{segment(link_id)}",
            **kwargs,
        ).status_code

    def put_test_run_lock(
        self,
        test_run_id: int,
        locked: bool,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Lock or unlock a test run.

        Args:
            test_run_id: The API ID of the test run
            locked: The lock state to set

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"testruns/{segment(test_run_id)}/lock",
            params,
            json={"locked": locked},
            **kwargs,
        ).status_code

    def post_test_run_tag(
        self,
        test_run_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add an existing tag to a test run.

        Args:
            test_run_id: The API ID of the test run
            tag_id: The API ID of the tag to add

        Returns: the client response
        """
        body = {"tag": tag_id}
        return self._post(
            f"testruns/{segment(test_run_id)}/tags", body, params, **kwargs
        )

    def delete_test_run_tag(self, test_run_id: int, tag_id: int, **kwargs) -> int:
        """
        Remove a tag from a test run.

        Args:
            test_run_id: The API ID of the test run
            tag_id: The API ID of the tag to remove

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete,
            f"testruns/{segment(test_run_id)}/tags/{segment(tag_id)}",
            **kwargs,
        ).status_code

    def post_test_run_updated_test_case(
        self,
        test_run_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a new test run version with Not run status that reflects the
        newest test case version (makeTestRunCurrent).

        Args:
            test_run_id: The API ID of the test run

        Returns: the client response
        """
        return self._post(
            f"testruns/{segment(test_run_id)}/updatedtestcase", None, params, **kwargs
        )

    def post_test_run_attachment(
        self,
        test_run_id: int,
        attachment_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add an existing attachment to a test run.

        Args:
            test_run_id: The API ID of the test run
            attachment_id: The API ID of the attachment to add

        Returns: the client response
        """
        body = {"attachment": attachment_id}
        return self._post(
            f"testruns/{segment(test_run_id)}/attachments", body, params, **kwargs
        )

    def delete_test_run_attachment(
        self, test_run_id: int, attachment_id: int, **kwargs
    ) -> int:
        """
        Remove an attachment from a test run.

        Args:
            test_run_id: The API ID of the test run
            attachment_id: The API ID of the attachment to remove

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete,
            f"testruns/{segment(test_run_id)}/attachments/{segment(attachment_id)}",
            **kwargs,
        ).status_code

    def _get_all(
        self,
        resource_path: str,
        params: dict | None,
        allowed_results_per_page: int,
        **kwargs,
    ):
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def _get(self, resource_path: str, params: dict | None, **kwargs) -> ClientResponse:
        return ClientResponse.from_response(
            self._call(self.client.get, resource_path, params, **kwargs)
        )

    def _post(
        self, resource_path: str, body: dict | None, params: dict | None, **kwargs
    ) -> ClientResponse:
        return ClientResponse.from_response(
            self._call(self.client.post, resource_path, params, json=body, **kwargs)
        )

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
