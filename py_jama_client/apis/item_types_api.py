"""
Item Types API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> item_types_api = ItemTypesAPI(client)
    >>> item_types = item_types_api.get_item_types()
"""

import logging

from py_jama_client.apis._include import with_include
from py_jama_client.apis._path import segment
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all item types of the across all projects of
        the Jama Connect instance.

        Args:
            include: links to include as full objects in the linked map
            allowed_results_per_page: Number of results per page

        Returns: An array of dictionary objects

        """
        params = with_include(params, include)
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_type(
        self,
        item_type_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Gets item type information for a specific item type id.

        Args:
            include: links to include as full objects in the linked map
            item_type_id: The api id of the item type to fetch

        Returns: JSON object

        """
        params = with_include(params, include)
        resource_path = f"itemtypes/{segment(item_type_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_item_type(
        self,
        item_type: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create an item type. Admin operation; implemented from the REST
        docs and not exercised against a live instance.

        Args:
            item_type: The request body. The documented fields are typeKey,
                display, displayPlural, description, image, category and
                widgets (a list of {"name": ..., "synchronize": ...}).
            params: optional query parameters

        Returns: the client response; the docs show the new item type ID as data
        """
        return ClientResponse.from_response(
            self._call(self.client.post, "itemtypes", params, json=item_type, **kwargs)
        )

    def post_item_type_field(
        self,
        item_type_id: int,
        field: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a field on an item type. Admin operation; implemented from the
        REST docs and not exercised against a live instance.

        Args:
            item_type_id: The API ID of the item type
            field: The request body. The documented fields are name, label,
                fieldType, readOnly, readOnlyAllowApiOverwrite, required,
                triggerSuspect, synchronize, pickList, textType and infotip.
            params: optional query parameters

        Returns: the client response
        """
        return ClientResponse.from_response(
            self._call(
                self.client.post,
                f"itemtypes/{segment(item_type_id)}/fields",
                params,
                json=field,
                **kwargs,
            )
        )

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
