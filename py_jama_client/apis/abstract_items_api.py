"""
Abstract Items API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> abstract_items_api = AbstractItemsAPI(client)
    >>> abstract_items = abstract_items_api.get_abstract_items()
"""

import logging
from typing import Optional

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
        project: list[int] = None,
        item_type: list[int] = None,
        document_key: list[str] = None,
        release: list[int] = None,
        created_date: list[str] = None,
        modified_date: list[str] = None,
        last_activity_date: list[str] = None,
        contains: list[str] = None,
        sort_by: list[str] = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Search for items, test plans, test cycles, test runs, or attachments
        GET: /abstractitems/

        Args:
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
        """

        # Add each parameter that is not null to the request.
        if params is None:
            params = {}

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

        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_abstract_item(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get any item, test plan, test cycle, test run, or attachment with the specified ID
        GET: /abstractitems/{item_id}

        Args:
            item_id: the item id of the item to fetch
        """
        resource_path = f"abstractitems/{item_id}"
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
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all versioned relationships that were associated to the item at the specified time
        GET: /abstractitems/{item_id}/versionedrelationships

        Args:
            item_id: item resource id
            timestamp: Get relationships for the specified item at this date and time.
                Requires ISO8601 formatting (milliseconds or seconds) - "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
                or "yyyy-MM-dd'T'HH:mm:ssZ"
        """
        resource_path = f"{self.resource_path}/{item_id}/versionedrelationships"
        req_params = {"timestamp": timestamp}
        if params is None:
            params = req_params
        else:
            params.update(req_params)
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
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID
        GET: /abstractitems/{item_id}/versions

        Args:
            item_id: the item id of the item to fetch

        Returns: JSON array with all versions for the item
        """
        resource_path = f"{self.resource_path}/{item_id}/versions"
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
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the numbered version for the item with the specified ID
        GET: /abstractitems/{item_id}/versions/{version_num}/

        Args:
            item_id: the item id of the item to fetch
            version_num: the version number for the item
        """
        resource_path = f"{self.resource_path}/{item_id}/versions/{version_num}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_versioned_item(
        self,
        item_id: int,
        version_num: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the snapshot of the item at the specified version
        GET: /abstractitems/{item_id}/versions/{version_num}/versioneditem/

        Args:
            item_id: the item id of the item to fetch
            version_num: the version number for the item
        """
        resource_path = (
            f"{self.resource_path}/{item_id}/versions/{version_num}/versioneditem"
        )
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
