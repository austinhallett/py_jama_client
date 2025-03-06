"""
Pick List Options API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> pick_list_options_api = PickListOptionsAPI(client)
    >>> pick_list_options = pick_list_options_api.get_pick_list_options(
            pick_list_id=10)
"""

import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class PickListOptionsAPI:
    client: JamaClient

    resource_path = "picklistoptions"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_pick_list_option(
        self,
        pick_list_option_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Fetches a single picklist option from the API
        Args:
            pick_list_option_id: The API ID of the picklist option to fetch

        Returns: A dictonary object representing the picklist option.

        """
        resource_path = f"picklistoptions/{pick_list_option_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
