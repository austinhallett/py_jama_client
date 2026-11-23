"""
Pick Lists API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> pick_lists_api = PickListsAPI(client)
    >>> pick_lists = pick_lists_api.get_pick_lists()
"""

import logging

from py_jama_client.apis._include import with_include
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class PickListsAPI:
    client: JamaClient

    resource_path = "picklists"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_pick_lists(
        self,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the pick lists

        Args:
            include: links to include as full objects in the linked map
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects
        """
        params = with_include(params, include)
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_pick_list(
        self,
        pick_list_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Gets all a singular picklist

        Args:
            include: links to include as full objects in the linked map
            pick_list_id: The API id of the pick list to fetch

        Returns: a dictionary object representing the picklist.
        """
        params = with_include(params, include)
        resource_path = f"picklists/{segment(pick_list_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_pick_list_options(
        self,
        pick_list_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Gets all all the picklist options for a single picklist
        Args:
            include: links to include as full objects in the linked map
            pick_list_id: the api id of the picklist to fetch options for.
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the
        picklist options.
        """
        params = with_include(params, include)
        resource_path = f"picklists/{segment(pick_list_id)}/options"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_pick_list(
        self,
        name: str,
        description: str,
        pick_list_type: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a pick list. Admin operation; implemented from the REST docs
        and not exercised against a live instance.

        Args:
            name: The pick list name
            description: The pick list description
            pick_list_type: The pick list type ID; the docs say 0 to 3 for a
                standard pick list and 4 for a lookup matrix pick list
            params: optional query parameters

        Returns: the client response; the new pick list ID is in meta.id
        """
        body = {"name": name, "description": description, "type": pick_list_type}
        return ClientResponse.from_response(
            self._call(self.client.post, "picklists", params, json=body, **kwargs)
        )

    def delete_pick_list(self, pick_list_id: int, **kwargs) -> int:
        """
        Delete a pick list. Admin operation; implemented from the REST docs
        and not exercised against a live instance.

        Args:
            pick_list_id: The API ID of the pick list

        Returns:
            (int): The response status code.
        """
        return self._call(
            self.client.delete, f"picklists/{segment(pick_list_id)}", **kwargs
        ).status_code

    def post_pick_list_option(
        self,
        pick_list_id: int,
        option: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create an option on a pick list. Admin operation; implemented from the
        REST docs and not exercised against a live instance.

        Args:
            pick_list_id: The API ID of the pick list
            option: The request body. The documented fields are name,
                description, value, color, sortOrder, infotip and default.
            params: optional query parameters

        Returns: the client response; the new option ID is in meta.id
        """
        return ClientResponse.from_response(
            self._call(
                self.client.post,
                f"picklists/{segment(pick_list_id)}/options",
                params,
                json=option,
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
