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

from py_jama_client.apis._include import with_include
from py_jama_client.apis._path import segment
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Fetches a single picklist option from the API
        Args:
            include: links to include as full objects in the linked map
            pick_list_option_id: The API ID of the picklist option to fetch

        Returns: A dictonary object representing the picklist option.

        """
        params = with_include(params, include)
        resource_path = f"picklistoptions/{segment(pick_list_option_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_pick_list_option(
        self,
        pick_list_option_id: int,
        option: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a pick list option. Admin operation; implemented from the REST
        docs and not exercised against a live instance.

        Args:
            pick_list_option_id: The API ID of the pick list option
            option: The request body. The documented fields are name,
                description, value, color, sortOrder, infotip and default.
            params: optional query parameters

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.put,
            f"picklistoptions/{segment(pick_list_option_id)}",
            params,
            json=option,
            **kwargs,
        ).status_code

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
