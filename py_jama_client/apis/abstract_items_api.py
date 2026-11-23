"""
Abstract Items API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> abstract_items_api = AbstractItemsAPI(client)
    >>> abstract_items = abstract_items_api.get_abstract_items()
"""

import logging

from py_jama_client.apis._include import with_include
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class AbstractItemsAPI:
    client: JamaClient

    resource_path = "abstractitems"

    def __init__(self, client: JamaClient) -> None:
        self.client = client

    def get_abstract_items(
        self,
        project: int | list[int] | None = None,
        item_type: int | list[int] | None = None,
        document_key: str | list[str] | None = None,
        release: int | list[int] | None = None,
        created_date: str | list[str] | None = None,
        modified_date: str | list[str] | None = None,
        last_activity_date: str | list[str] | None = None,
        contains: str | list[str] | None = None,
        sort_by: str | list[str] | None = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *,
        params: dict | None = None,
        include_wildcard: bool | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Search for items, test plans, test cycles, test runs, or attachments
        GET: /abstractitems/

        Args:
            include: links to include as full objects in the linked map
            project: list of project resource ids
            item_type: list of item type resource ids
            document_key: list of document keys
            release: list of release source ids
            created_date: Filter datetime fields after a single date or within a range of values.
                Provide one or two values in ISO8601 format (milliseconds or seconds) -
                "yyyy-MM-dd'T'HH:mm:ss.SSSZ" or "yyyy-MM-dd'T'HH:mm:ssZ"
            modified_date: Filter datetime fields after a single date or within a range of values.
                Provide one or two values in ISO8601 format (milliseconds or seconds) -
                "yyyy-MM-dd'T'HH:mm:ss.SSSZ" or "yyyy-MM-dd'T'HH:mm:ssZ"
            last_activity_date: Filter datetime fields after a single date or within a range of values.
                Provide one or two values in ISO8601 format (milliseconds or seconds) -
                "yyyy-MM-dd'T'HH:mm:ss.SSSZ" or "yyyy-MM-dd'T'HH:mm:ssZ"
            contains: Filter on the text contents of the item. Strings taken literally.
                Multiple 'contains' values will be bitwise ORed.
            sort_by: Sort orders can be added with the name of the field by which to sort, followed by .asc
                or .desc (e.g. 'name.asc' or 'modifiedDate.desc'). If not set, this defaults to sorting
                by sequence.asc and then documentKey.asc
            include_wildcard: Filter the search results with the specific
                'contains' value, maximizing the results based on variations of
                the word (sent as includeWildcard; overrides the same key in
                params)
        """
        params = with_include(params, include)

        # Add each parameter that is not null to the request.
        params = dict(params or {})

        if project is not None:
            params.update({"project": project})

        if item_type is not None:
            params.update({"itemType": item_type})

        if document_key is not None:
            params.update({"documentKey": document_key})

        if release is not None:
            params.update({"release": release})

        if created_date is not None:
            params.update({"createdDate": created_date})

        if modified_date is not None:
            params.update({"modifiedDate": modified_date})

        if last_activity_date is not None:
            params.update({"lastActivityDate": last_activity_date})

        if contains is not None:
            params.update({"contains": contains})

        if sort_by is not None:
            params.update({"sortBy": sort_by})

        if include_wildcard is not None:
            params.update({"includeWildcard": include_wildcard})

        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_abstract_item(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get any item, test plan, test cycle, test run, or attachment with the specified ID
        GET: /abstractitems/{item_id}

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
        """
        params = with_include(params, include)
        resource_path = f"abstractitems/{segment(item_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_versioned_relationships(
        self,
        item_id: int,
        timestamp: str,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get all versioned relationships that were associated to the item at the specified time
        GET: /abstractitems/{item_id}/versionedrelationships

        Args:
            include: links to include as full objects in the linked map
            item_id: item resource id
            timestamp: Get relationships for the specified item at this date and time.
                Requires ISO8601 formatting (milliseconds or seconds) - "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
                or "yyyy-MM-dd'T'HH:mm:ssZ"
        """
        params = with_include(params, include)
        resource_path = (
            f"{self.resource_path}/{segment(item_id)}/versionedrelationships"
        )
        params = {**(params or {}), "timestamp": timestamp}
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_abstract_item_versions(
        self,
        item_id: int,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID
        GET: /abstractitems/{item_id}/versions

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch

        Returns: JSON array with all versions for the item
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(item_id)}/versions"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_abstract_item_version(
        self,
        item_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the numbered version for the item with the specified ID
        GET: /abstractitems/{item_id}/versions/{version_num}/

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
            version_num: the version number for the item
        """
        params = with_include(params, include)
        resource_path = (
            f"{self.resource_path}/{segment(item_id)}/versions/{segment(version_num)}"
        )
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_versioned_item(
        self,
        item_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the snapshot of the item at the specified version
        GET: /abstractitems/{item_id}/versions/{version_num}/versioneditem/

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
            version_num: the version number for the item
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(item_id)}/versions/{segment(version_num)}/versioneditem"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
