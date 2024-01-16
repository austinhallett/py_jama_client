"""
Abstract Items API module

Example usage:

    >>> from py_jama_rest_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> abstract_items_api = AbstractItemsAPI(client)
    >>> abstract_items = abstract_items_api.get_abstract_items()    
"""

import json
import logging
from typing import Optional
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.client import BaseClient
from py_jama_client.response import ClientResponse
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_client_logger = logging.getLogger("py_jama_rest_client")


class AbstractItemsAPI:
    client: BaseClient

    resource_path = "abstractitems"

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
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return all items that match the query parameters entered.

        Args:
            project:            Array[integer]
            item_type:          Array[integer]
            document_key:       Array[string]
            release:            Array[integer]
            created_date:       Array[string]
            modified_date:      Array[string]
            last_activity_date: Array[string]
            contains:           Array[string]
            sort_by:            Array[string]

        Returns:
            A JSON Array of items.

        """
        resource_path = "abstractitems"

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

        return self.client.get_all(resource_path, params, **kwargs)

    def get_abstract_item(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return an item, test plan, test cycle, test run, or attachment with the specified ID
        Args:
            item_id: the item id of the item to fetch

        Returns: a dictonary object representing the abstract item

        """
        resource_path = f"abstractitems/{item_id}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_item_versions(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID

        Args:
            item_id: the item id of the item to fetch

        Returns: JSON array with all versions for the item
        """
        resource_path = f"abstractitems/{item_id}/versions"
        return self.client.get_all(resource_path, params, **kwargs)

    def get_abtract_item_version(
        self,
        item_id: int,
        version_num: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the numbered version for the item with the specified ID

        Args:
            item_id: the item id of the item to fetch
            version_num: the version number for the item

        Returns: a dictionary object representing the numbered version
        """
        resource_path = f"abstractitems/{item_id}/versions/{version_num}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
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

        Args:
            item_id: the item id of the item to fetch
            version_num: the version number for the item

        Returns: a dictionary object representing the versioned item
        """
        resource_path = f"abstractitems/{item_id}/versions/{version_num}/versioneditem"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)
