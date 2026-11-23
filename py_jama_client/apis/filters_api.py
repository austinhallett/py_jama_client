"""
Filters API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> filters_api = FiltersAPI(client)
    >>> results = filters_api.get_filter_results(FILTER_ID)
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class FiltersAPI:
    client: JamaClient

    resource_path = "filters"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_filters(
        self,
        *,
        params: dict | None = None,
        author: int | None = None,
        filter_scope: list[str] | None = None,
        access_specifier: str | None = None,
        project: int | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all filters viewable by the current user

        Args:
            include: links to include as full objects in the linked map
            params: optional query parameters
            author: only filters by the user with this API ID (sent as author)
            filter_scope: list of scopes (ALL_PROJECTS, BOUND_PROJECT,
                CURRENT_PROJECT); more than one scope can be selected (sent as
                filterScope)
            access_specifier: PUBLIC, PRIVATE or PUBLIC_AND_PRIVATE (sent as
                accessSpecifier)
            project: the project API ID (sent as project)
            Each of these overrides the same key in params.
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of filters

        docs: https://rest.jamasoftware.com/#operation_getFilters
        """
        params = with_include(params, include)
        params = with_query(
            params,
            author=author,
            filterScope=filter_scope,
            accessSpecifier=access_specifier,
            project=project,
        )
        resource_path = "filters"
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_filter(
        self,
        filter_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the filter with the specified ID

        Args:
            include: links to include as full objects in the linked map
            filter_id: The ID of the filter to fetch

        Returns: the client response

        docs: https://rest.jamasoftware.com/#operation_getFilter
        """
        params = with_include(params, include)
        resource_path = f"filters/{segment(filter_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err)) from err
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_filter_count(
        self,
        filter_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ):
        """
        Get the count of results for the filter with the specified ID

        Args:
            filter_id: The ID of the filter to count the results of

        Returns: the client response, whose data is the integer count

        docs: https://rest.jamasoftware.com/#operation_getCount
        """
        resource_path = f"filters/{segment(filter_id)}/count"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err)) from err
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_filter_results(
        self,
        filter_id: int,
        project_id: int | None = None,
        *,
        params: dict | None = None,
        last_activity_date: list[str] | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all results items for the filter with the specified ID

        Args:
            include: links to include as full objects in the linked map
            filter_id: The ID of the filter to fetch the results for.
            project_id: Use this only for filters that run on any project,
                where projectScope is CURRENT
            last_activity_date: Filter datetime fields after a single date or
                within a range of values. Provide one or two values in ISO8601
                format (milliseconds or seconds) -
                "yyyy-MM-dd'T'HH:mm:ss.SSSZ" or "yyyy-MM-dd'T'HH:mm:ssZ"
                (sent as lastActivityDate; overrides the same key in params)
            allowed_results_per_page: Number of results per page

        Returns:
            A List of items that match the filter.

        """
        params = with_include(params, include)
        resource_path = f"filters/{segment(filter_id)}/results"

        params = {
            **(params or {}),
            **({"project": project_id} if project_id is not None else {}),
            **(
                {"lastActivityDate": last_activity_date}
                if last_activity_date is not None
                else {}
            ),
        }

        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )
