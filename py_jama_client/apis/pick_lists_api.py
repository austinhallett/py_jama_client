"""
Pick Lists API module

Example usage:

    >>> from py_jama_rest_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> pick_lists_api = PickListsAPI(client)
    >>> pick_lists = pick_lists_api.get_pick_lists()    
"""

import json
import logging
from typing import Optional
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.client import BaseClient
from py_jama_client.response import ClientResponse
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_client_logger = logging.getLogger("py_jama_rest_client")


class PickListsAPI:
    client: BaseClient

    resource_path = "picklists"

    def __init__(self, client: BaseClient):
        self.client = client

    def get_pick_lists(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the pick lists

        Args:
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects
        """
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_pick_list(
        self,
        pick_list_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets all a singular picklist

        Args:
            pick_list_id: The API id of the pick list to fetch

        Returns: a dictionary object representing the picklist.
        """
        resource_path = f"picklists/{pick_list_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)
