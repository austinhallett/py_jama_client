"""
Item Types API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> item_types_api = ItemTypesAPI(client)
    >>> item_types = item_types_api.get_item_types()
"""

import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class ItemTypesAPI:
    client: JamaClient

    resource_path = "itemtypes"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_item_types(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all item types of the across all projects of
        the Jama Connect instance.

        Args:
            allowed_results_per_page: Number of results per page

        Returns: An array of dictionary objects

        """
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_type(
        self,
        item_type_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets item type information for a specific item type id.

        Args:
            item_type_id: The api id of the item type to fetch

        Returns: JSON object

        """
        resource_path = f"itemtypes/{item_type_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
