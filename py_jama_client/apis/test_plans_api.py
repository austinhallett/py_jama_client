"""
Test Plans API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> test_plans_api = TestPlansAPI(client)
    >>> test_plans = test_plans_api.get_test_plans()
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class TestPlansAPI:
    client: JamaClient

    resource_path = "testplans"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_test_plans(
        self,
        *,
        params: dict | None = None,
        project: int | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all test plans viewable by the current user

        Args:
            include: links to include as full objects in the linked map
            params: optional query parameters
            project: only test plans of the project with this API ID (sent as
                project; overrides the same key in params)
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of test plans
        """
        params = with_include(params, include)
        params = with_query(params, project=project)
        return self.client.get_all(
            "testplans",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the test plan with the specified ID

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters

        Returns: the client response, whose data is the test plan
        """
        params = with_include(params, include)
        return self._get(f"testplans/{segment(test_plan_id)}", params, **kwargs)

    def get_test_plan_activities(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the activity stream of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of activities
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/activities",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_attachments(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the attachments on a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of attachments
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/attachments",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_comments(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        root_comments_only: bool | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the comments on a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            root_comments_only: if True, get only root comments, without their
                replies (sent as rootCommentsOnly; overrides the same key in
                params)
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of comments
        """
        params = with_include(params, include)
        params = with_query(params, rootCommentsOnly=root_comments_only)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/comments",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_downstream_related(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the items downstream of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of items
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/downstreamrelated",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_downstream_relationships(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the downstream relationships of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of relationships
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/downstreamrelationships",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_upstream_related(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the items upstream of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of items
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/upstreamrelated",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_upstream_relationships(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the upstream relationships of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of relationships
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/upstreamrelationships",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_links(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the links on a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of links
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/links",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_tags(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the tags on a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of tags
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/tags",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_test_cycles(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the test cycles of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of test cycles
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/testcycles",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_groups(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the test groups of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of test groups
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/testgroups",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_versions(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the versions of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of versions
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/versions",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_plan_link(
        self,
        test_plan_id: int,
        link_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a link on a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            link_id: The ID of the link
            params: optional query parameters

        Returns: the client response, whose data is the link
        """
        params = with_include(params, include)
        return self._get(
            f"testplans/{segment(test_plan_id)}/links/{segment(link_id)}",
            params,
            **kwargs,
        )

    def get_test_plan_lock(
        self,
        test_plan_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the locked state, last locked date and last locked by user of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            params: optional query parameters

        Returns: the client response, whose data is the lock information
        """
        params = with_include(params, include)
        return self._get(f"testplans/{segment(test_plan_id)}/lock", params, **kwargs)

    def get_test_plan_tag(
        self,
        test_plan_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a tag on a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            tag_id: The API ID of the tag on the test plan
            params: optional query parameters

        Returns: the client response, whose data is the tag
        """
        params = with_include(params, include)
        return self._get(
            f"testplans/{segment(test_plan_id)}/tags/{segment(tag_id)}",
            params,
            **kwargs,
        )

    def get_test_group(
        self,
        test_plan_id: int,
        test_group_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a test group of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            test_group_id: The API ID of the test group
            params: optional query parameters

        Returns: the client response, whose data is the test group
        """
        params = with_include(params, include)
        return self._get(
            f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}",
            params,
            **kwargs,
        )

    def get_test_group_test_cases(
        self,
        test_plan_id: int,
        test_group_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the test cases in a test group

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            test_group_id: The API ID of the test group
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of test cases
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}/testcases",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_group_test_case(
        self,
        test_plan_id: int,
        test_group_id: int,
        test_case_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a test case in a test group

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            test_group_id: The API ID of the test group
            test_case_id: The API ID of the test case
            params: optional query parameters

        Returns: the client response, whose data is the test case
        """
        params = with_include(params, include)
        return self._get(
            f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}/testcases/{segment(test_case_id)}",
            params,
            **kwargs,
        )

    def get_test_plan_version(
        self,
        test_plan_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the numbered version of a test plan

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            version_num: The version number
            params: optional query parameters

        Returns: the client response, whose data is the version
        """
        params = with_include(params, include)
        return self._get(
            f"testplans/{segment(test_plan_id)}/versions/{segment(version_num)}",
            params,
            **kwargs,
        )

    def get_test_plan_versioned_item(
        self,
        test_plan_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the snapshot of a test plan at the numbered version

        Args:
            include: links to include as full objects in the linked map
            test_plan_id: The API ID of the test plan
            version_num: The version number
            params: optional query parameters

        Returns: the client response, whose data is the versioned test plan
        """
        params = with_include(params, include)
        return self._get(
            f"testplans/{segment(test_plan_id)}/versions/{segment(version_num)}/versioneditem",
            params,
            **kwargs,
        )

    def post_test_plan(
        self,
        project_id: int,
        fields: dict,
        *,
        params: dict | None = None,
        parent_test_plan_folder_id: int | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a new test plan in a project.

        Args:
            project_id (int): The API ID of the project to create the test
                plan in.
            fields (dict): Field names to values, e.g. {"name": "Plan"}.
            parent_test_plan_folder_id (int): The API ID of the test plan
                folder to create the test plan in. Omitted from the request
                when None.

        Returns:
            (ClientResponse): The response; the new test plan ID is in
                meta.id.
        """
        body = {"fields": fields, "project": project_id}
        if parent_test_plan_folder_id is not None:
            body["parentTestPlanFolderId"] = parent_test_plan_folder_id
        return self._post("testplans", body, params, **kwargs)

    def post_test_group(
        self,
        test_plan_id: int,
        name: str,
        assigned_to: int | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a new test group in a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            name (str): The name of the new test group.
            assigned_to (int): The API ID of the user the group is assigned
                to. Omitted from the request when None.

        Returns:
            (ClientResponse): The response; the new test group ID is in
                meta.id.
        """
        body: dict = {"name": name}
        if assigned_to is not None:
            body["assignedTo"] = assigned_to
        return self._post(
            f"testplans/{segment(test_plan_id)}/testgroups", body, params, **kwargs
        )

    def post_test_group_test_case(
        self,
        test_plan_id: int,
        test_group_id: int,
        test_case_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add an existing test case to a test group.

        Args:
            test_plan_id (int): The API ID of the test plan.
            test_group_id (int): The API ID of the test group.
            test_case_id (int): The API ID of the test case item to add.

        Returns:
            (ClientResponse): The response of the server.
        """
        body = {"testCase": test_case_id}
        resource_path = f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}/testcases"
        return self._post(resource_path, body, params, **kwargs)

    def delete_test_plan(self, test_plan_id: int, **kwargs) -> int:
        """
        Delete the test plan with the specified ID.

        Args:
            test_plan_id (int): The API ID of the test plan.

        Returns:
            (int): The success status code.
        """
        try:
            response = self.client.delete(
                f"testplans/{segment(test_plan_id)}", **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def patch_test_plan(
        self,
        test_plan_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Patch a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            patches (list[dict]): Patch operations, each with op, path and
                value, e.g. {"op": "replace", "path": "/fields/name",
                "value": "New name"}.

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.patch,
            f"testplans/{segment(test_plan_id)}",
            params,
            json=patches,
            **kwargs,
        ).status_code

    def put_test_plan(
        self,
        test_plan_id: int,
        fields: dict,
        *,
        params: dict | None = None,
        location: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a test plan. PUT replaces all fields: fields not passed are
        cleared. Use patch_test_plan for partial updates.

        Args:
            test_plan_id (int): The API ID of the test plan.
            fields (dict): Field names to values, e.g. {"name": "Plan"}.
            location (dict): Where to locate the test plan, e.g.
                {"parent": {"item": 123}, "sortOrder": 1}; parent is one of
                {"item": id} or {"project": id}. Omitted from the request
                when None.

        Returns:
            (int): The response status code.
        """
        body: dict = {"fields": fields}
        if location is not None:
            body["location"] = location
        return self._call(
            self.client.put,
            f"testplans/{segment(test_plan_id)}",
            params,
            json=body,
            **kwargs,
        ).status_code

    def put_test_plan_archived(
        self,
        test_plan_id: int,
        archived: bool,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Archive or unarchive a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            archived (bool): The archived state to set.

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"testplans/{segment(test_plan_id)}/archived",
            params,
            json={"archived": archived},
            **kwargs,
        ).status_code

    def post_test_plan_tag(
        self,
        test_plan_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add an existing tag to a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            tag_id (int): The API ID of the tag to add.

        Returns:
            (ClientResponse): The response of the server.
        """
        body = {"tag": tag_id}
        return self._post(
            f"testplans/{segment(test_plan_id)}/tags", body, params, **kwargs
        )

    def delete_test_plan_tag(self, test_plan_id: int, tag_id: int, **kwargs) -> int:
        """
        Remove a tag from a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            tag_id (int): The API ID of the tag to remove.

        Returns:
            (int): The success status code.
        """
        return self._call(
            self.client.delete,
            f"testplans/{segment(test_plan_id)}/tags/{segment(tag_id)}",
            **kwargs,
        ).status_code

    def post_test_plan_link(
        self,
        test_plan_id: int,
        url: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add a URL link to a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            url (str): The URL to link to.
            description (str): The link text.

        Returns:
            (ClientResponse): The response; the new link ID is in meta.id.
        """
        body = {"url": url, "description": description}
        return self._post(
            f"testplans/{segment(test_plan_id)}/links", body, params, **kwargs
        )

    def put_test_plan_link(
        self,
        test_plan_id: int,
        link_id: int,
        url: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a URL link on a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            link_id (int): The ID of the link.
            url (str): The URL to link to.
            description (str): The link text.

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"testplans/{segment(test_plan_id)}/links/{segment(link_id)}",
            params,
            json={"url": url, "description": description},
            **kwargs,
        ).status_code

    def delete_test_plan_link(self, test_plan_id: int, link_id: int, **kwargs) -> int:
        """
        Remove a link from a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            link_id (int): The ID of the link.

        Returns:
            (int): The success status code.
        """
        return self._call(
            self.client.delete,
            f"testplans/{segment(test_plan_id)}/links/{segment(link_id)}",
            **kwargs,
        ).status_code

    def put_test_plan_lock(
        self,
        test_plan_id: int,
        locked: bool,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Lock or unlock a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            locked (bool): The lock state to set.

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"testplans/{segment(test_plan_id)}/lock",
            params,
            json={"locked": locked},
            **kwargs,
        ).status_code

    def post_test_plan_attachment(
        self,
        test_plan_id: int,
        attachment_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Add an existing attachment to a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            attachment_id (int): The API ID of the attachment to add.

        Returns:
            (ClientResponse): The response of the server.
        """
        body = {"attachment": attachment_id}
        return self._post(
            f"testplans/{segment(test_plan_id)}/attachments", body, params, **kwargs
        )

    def delete_test_plan_attachment(
        self, test_plan_id: int, attachment_id: int, **kwargs
    ) -> int:
        """
        Remove an attachment from a test plan.

        Args:
            test_plan_id (int): The API ID of the test plan.
            attachment_id (int): The API ID of the attachment to remove.

        Returns:
            (int): The success status code.
        """
        return self._call(
            self.client.delete,
            f"testplans/{segment(test_plan_id)}/attachments/{segment(attachment_id)}",
            **kwargs,
        ).status_code

    def put_test_group(
        self,
        test_plan_id: int,
        test_group_id: int,
        name: str,
        assigned_to: int | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a test group. PUT replaces the whole group, so
        assigned_to=None clears an existing assignee.

        Args:
            test_plan_id (int): The API ID of the test plan.
            test_group_id (int): The API ID of the test group.
            name (str): The new name of the test group.
            assigned_to (int): The API ID of the user the group is assigned
                to. Omitted from the request when None.

        Returns:
            (int): The response status code.
        """
        body: dict = {"name": name}
        if assigned_to is not None:
            body["assignedTo"] = assigned_to
        return self._call(
            self.client.put,
            f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}",
            params,
            json=body,
            **kwargs,
        ).status_code

    def delete_test_group(self, test_plan_id: int, test_group_id: int, **kwargs) -> int:
        """
        Delete a test group.

        Args:
            test_plan_id (int): The API ID of the test plan.
            test_group_id (int): The API ID of the test group.

        Returns:
            (int): The success status code.
        """
        return self._call(
            self.client.delete,
            f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}",
            **kwargs,
        ).status_code

    def delete_test_group_test_case(
        self, test_plan_id: int, test_group_id: int, test_case_id: int, **kwargs
    ) -> int:
        """
        Remove a test case from a test group.

        Args:
            test_plan_id (int): The API ID of the test plan.
            test_group_id (int): The API ID of the test group.
            test_case_id (int): The API ID of the test case to remove.

        Returns:
            (int): The success status code.
        """
        return self._call(
            self.client.delete,
            f"testplans/{segment(test_plan_id)}/testgroups/{segment(test_group_id)}"
            f"/testcases/{segment(test_case_id)}",
            **kwargs,
        ).status_code

    def _post(
        self, resource_path: str, body: dict, params: dict | None, **kwargs
    ) -> ClientResponse:
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

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

    def post_testplans_testcycles(
        self,
        testplan_id: int,
        testcycle_name: str,
        start_date: str,
        end_date: str,
        testgroups_to_include: list[int] | None = None,
        testrun_status_to_include: list[str] | None = None,
        *,
        params: dict | None = None,
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
        resource_path = f"testplans/{segment(testplan_id)}/testcycles"
        fields = {"name": testcycle_name, "startDate": start_date, "endDate": end_date}
        test_run_gen_config: dict = {}
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
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))

        # Validate response
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
