"""
Items API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> items_api = ItemsAPI(client)
    >>> items = items_api.get_items(project_id=1)
"""

import logging
from typing import Literal, overload

import httpx

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class ItemsAPI:
    client: JamaClient

    resource_path = "items"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_items(
        self,
        project_id: int,
        *,
        params: dict | None = None,
        root_only: bool | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all items in the specified project.
        Args:
            include: links to include as full objects in the linked map
            project_id: the project ID
            root_only: if True, only get the root-level nodes of the item tree
                (sent as rootOnly; overrides the same key in params)
            allowed_results_per_page: number of results per page

        Returns: a Json array of item objects

        """
        params = with_include(params, include)

        params = {**(params or {}), "project": project_id}
        params = with_query(params, rootOnly=root_only)

        return self.client.get_all(
            self.resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        This method will return a singular item of a specified item id
        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch

        Returns: a dictonary object representing the item

        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(item_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_item(
        self,
        project_id: int,
        item_type_id: int,
        child_item_type_id: int,
        location: dict,
        fields: dict,
        global_id: str | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ):
        """
        This method will post a new item to Jama Connect.

        Args:
            project_id: (int) id of project
            item_type_id: (int) ID of an Item Type.
            child_item_type_id: (int) integer ID of an Item Type.
            location: (dict) the parent, naming exactly one of "item" or
                "project"; naming both is refused with a 400 ("parent
                location is ambiguous")
            fields: (dict) dictionary item field data.
        Returns:
            newly created item

        location is sent as {"parent": location}, e.g. {"item": 5} or
        {"project": 1}.
        """
        params = {**(params or {})}

        body = {
            "project": project_id,
            "itemType": item_type_id,
            "childItemType": child_item_type_id,
            "location": {"parent": location},
            "fields": fields,
        }
        resource_path = f"{self.resource_path}"

        # we setting a global ID?
        if global_id is not None:
            body["globalId"] = global_id
            params["setGlobalIdManually"] = True

        try:
            response = self.client.post(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_item_tag(
        self,
        item_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Add an existing tag to the item with the specified ID
        Args:
            item_id: The API ID of the item to add a tag.
            tag_id: The API ID of the tag to add to the item.

        Returns: 201 if successful

        """
        body = {"tag": tag_id}
        resource_path = f"{self.resource_path}/{segment(item_id)}/tags"
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def post_item_sync(
        self,
        source_item: int,
        pool_item: int,
        *,
        params: dict | None,
        **kwargs,
    ):
        """
        add an item to an existing pool of global ids
        Args:
            source_item: integer API ID of the source item, this item will
                adopt the global id of the pool_item.
            pool_item: integer API ID of the item in the target global ID pool.

        Returns: the integer ID of the modified source item.
        """
        body = {"item": source_item}

        resource_path = f"{self.resource_path}/{segment(pool_item)}/synceditems"
        try:
            response = self.client.post(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_item_attachment(
        self,
        item_id: int,
        attachment_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Add an existing attachment to the item with the specified ID
        :param item_id: this is the ID of the item
        :param attachment_id: The ID of the attachment
        :return: 201 if successful / the response status of the post operation
        """
        body = {"attachment": attachment_id}
        resource_path = f"items/{segment(item_id)}/attachments"
        try:
            response = self.client.post(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def put_item(
        self,
        project_id: int,
        item_id: int,
        item_type_id: int,
        child_item_type_id: int,
        location: dict,
        fields: dict,
        *,
        params: dict | None = None,
        set_global_id_manually: bool | None = None,
        global_id: str | None = None,
        **kwargs,
    ):
        """
        This method will PUT a new item to Jama Connect.
        Args:
            project: integer representing the project to which this item is to
                be posted
            item_id: integer representing the item which is to be updated
            item_type_id: integer ID of an Item Type.
            child_item_type_id: integer ID of an Item Type.
            location: dictionary with a key of 'item' or 'project' and a value
                with the ID of the parent
            fields: dictionary item field data.
            set_global_id_manually: must be True to set the item's Global ID
                with global_id (sent as setGlobalIdManually; overrides the
                same key in params)
            global_id: the item's Global ID, sent only when not None
        Returns: integer ID of the successfully posted item or None if there
        was an error.
        """

        body = {
            "project": project_id,
            "itemType": item_type_id,
            "childItemType": child_item_type_id,
            "location": {"parent": location},
            "fields": fields,
        }
        if global_id is not None:
            body["globalId"] = global_id
        params = with_query(params, setGlobalIdManually=set_global_id_manually)
        resource_path = f"items/{segment(item_id)}"
        try:
            response = self.client.put(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    @overload
    def patch_item(
        self,
        item_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        return_item: Literal[True],
        **kwargs,
    ) -> ClientResponse: ...

    @overload
    def patch_item(
        self,
        item_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        return_item: Literal[False] | None = None,
        **kwargs,
    ) -> int: ...

    @overload
    def patch_item(
        self,
        item_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        return_item: bool | None = None,
        **kwargs,
    ) -> int | ClientResponse: ...

    def patch_item(
        self,
        item_id: int,
        patches: list[dict],
        *,
        params: dict | None = None,
        return_item: bool | None = None,
        **kwargs,
    ) -> int | ClientResponse:
        """
        This method will patch an item.
        Args:
            item_id: the API ID of the item that is to be patched
            patches: An array of dicts, that represent patch operations each
                dict should have the following entries
             [
                {
                    "op": string,
                    "path": string,
                    "value": {}
                }
            ]

            return_item: whether the server returns the patched item in the
                response body (sent as returnItem; overrides the same key in
                params)

        Returns: The response status code, or with return_item=True the client
            response holding the patched item

        """
        params = with_query(params, returnItem=return_item)
        resource_path = f"items/{segment(item_id)}"
        headers = httpx.Headers({"Accept": "application/json"})
        headers.update(kwargs.pop("headers", None) or {})

        try:
            response = self.client.patch(
                resource_path,
                params,
                json=patches,
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))

        JamaClient.handle_response_status(response)
        if return_item:
            return ClientResponse.from_response(response)
        return response.status_code

    def delete_item(
        self,
        item_id: int,
        **kwargs,
    ) -> int:
        """
        This method will delete an item in Jama Connect.

        Args:
            item_id: The jama connect API ID of the item to be deleted

        Returns: The success status code.
        """
        resource_path = f"items/{segment(item_id)}"
        try:
            response = self.client.delete(resource_path, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_tagged_items(
        self,
        tag_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all items tagged with the specified ID

        Args:
            include: links to include as full objects in the linked map
            tag_id: The ID of the tag to fetch the results for.
            allowed_results_per_page: Number of results per page

        Returns:
            A List of items that match the tag.

        """
        params = with_include(params, include)
        resource_path = f"tags/{segment(tag_id)}/items"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_upstream_relationships(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the upstream relationships for the item with the
        specified API ID.
        Args:
            include: links to include as full objects in the linked map
            item_id: the api id of the item
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the upstream
        relationships for the item.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/upstreamrelationships"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_downstream_related(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the downstream related items for the item with
        the specified API ID.

        Args:
            include: links to include as full objects in the linked map
            item_id: the api id of the item to fetch downstream items for
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the downstream
        related items for the specified item.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/downstreamrelated"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_downstream_relationships(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the downstream relationships for the item with
        the specified API ID.

        Args:
            include: links to include as full objects in the linked map
            item_id: the api id of the item

        Returns: an array of dictionary objects that represent the downstream
        relationships for the item.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/downstreamrelationships"
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_upstream_related(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Returns a list of all the upstream related items for the item with the
        specified API ID.

        Args:
            include: links to include as full objects in the linked map
            item_id: the api id of the item to fetch upstream items for

        Returns: an array of dictionary objects that represent the upstream
        related items for the specified item.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/upstreamrelated"
        return self.client.get_all(resource_path, params, **kwargs)

    def get_item_workflow_transitions(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get all valid workflow transitions that can be made with the specified
        API ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the api id of the item
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the workflow
        transitions for the item.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/workflowtransitionoptions"
        return self.client.get_all(resource_path, params, **kwargs)

    def get_item_children(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return list of the child items of the item passed to
        the function.
        Args:
            include: links to include as full objects in the linked map
            item_id: (int) The id of the item for which children items should
            be fetched allowed_results_per_page: Number of results per page

        Returns: a List of Objects that represent the children of the item
        passed in.
        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/children"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_synceditems(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all synchronized items for the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: The API id of the item being
            allowed_results_per_page: Number of results per page

        Returns: A list of JSON Objects representing the items that are in the
        same synchronization group as the specified item.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/synceditems"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_synceditems_status(
        self,
        item_id: int,
        synced_item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the sync status for the synced item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: The id of the item to compare against
            synced_item_id: the id of the item to check if it is in sync

        Returns: The response JSON from the API which contains a single field
            'inSync' with a boolean value.

        """
        params = with_include(params, include)
        resource_path = (
            f"items/{segment(item_id)}/synceditems/{segment(synced_item_id)}/syncstatus"
        )
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_version(
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

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
            version_num: the version number for the item

        Returns: a dictionary object representing the numbered version
        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/versions/{segment(version_num)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_versioned_item(
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

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
            version_num: the version number for the item

        Returns: a dictionary object representing the versioned item
        """
        params = with_include(params, include)
        resource_path = (
            f"items/{segment(item_id)}/versions/{segment(version_num)}/versioneditem"
        )
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_versions(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
            allowed_results_per_page: number of results per page

        Returns: JSON array with all versions for the item
        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/versions"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_lock(
        self,
        item_id: int,
        params: dict | None = None,
        *,
        include: list[str] | None = None,
    ):
        """
        Get the locked state, last locked date, and last locked by user for
        the item with the specified ID
        Args:
            include: links to include as full objects in the linked map
            item_id: The API ID of the item to get the lock info for.

        Returns:
            A JSON object with the lock information for the item with the
            specified ID.

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/lock"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_item_lock(
        self,
        item_id: int,
        locked: bool,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update the locked state of the item with the specified ID
        Args:
            item_id: the API id of the item to be updated
            locked: boolean lock state to apply to this item

        Returns:
            response status 200

        """
        body = {
            "locked": locked,
        }
        resource_path = f"items/{segment(item_id)}/lock"
        try:
            response = self.client.put(
                resource_path,
                params,
                json=body,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        return JamaClient.handle_response_status(response)

    def get_item_tags(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Return all tags for the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the item id of the item to fetch
            allowed_results_per_page: number of results

        Returns: a dictionary object representing the item's tags

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/tags"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_tag(
        self,
        item_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get a single tag on the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item
            tag_id: the API ID of the tag on the item

        Returns: a JSON object representing the tag

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/tags/{segment(tag_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_attachments(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all attachments on the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item
            allowed_results_per_page: number of results per page

        Returns: a JSON array of the attachments on the item

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/attachments"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_location(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the location of the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item

        Returns: a JSON object with the location of the item

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/location"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_parent(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the parent of the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item

        Returns: a JSON object representing the parent item

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/parent"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_activities(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all activities on the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item
            allowed_results_per_page: number of results per page

        Returns: a JSON array of the activities on the item

        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/activities"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_comments(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        root_comments_only: bool | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the comments on the item with the specified ID. The server lists
        top-level comments only, even with rootCommentsOnly=false; use
        CommentsAPI.get_comment_replies for replies.

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item
            root_comments_only: if True, get only root comments, without their
                replies (sent as rootCommentsOnly; overrides the same key in
                params)
            allowed_results_per_page: number of results per page

        Returns: the client response, whose data is the list of comments

        """
        params = with_include(params, include)
        params = with_query(params, rootCommentsOnly=root_comments_only)
        resource_path = f"items/{segment(item_id)}/comments"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def delete_item_tag(
        self,
        item_id: int,
        tag_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Remove a tag from the item with the specified ID. The tag itself is
        not deleted.

        Args:
            item_id: the API ID of the item
            tag_id: the API ID of the tag to remove from the item

        Returns: The response status code.

        """
        resource_path = f"items/{segment(item_id)}/tags/{segment(tag_id)}"
        try:
            response = self.client.delete(resource_path, params=params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_item_synceditem(
        self,
        item_id: int,
        synced_item_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Remove a synchronized item from the global ID pool of the item with the
        specified ID (break the sync).

        Args:
            item_id: the API ID of an item in the pool
            synced_item_id: the API ID of the item to remove from the pool

        Returns: The response status code.

        """
        resource_path = (
            f"items/{segment(item_id)}/synceditems/{segment(synced_item_id)}"
        )
        try:
            response = self.client.delete(resource_path, params=params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_item_attachment(
        self,
        item_id: int,
        attachment_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Remove an attachment from the item with the specified ID.

        Args:
            item_id: the API ID of the item
            attachment_id: the API ID of the attachment to remove from the item

        Returns: The response status code.

        """
        resource_path = f"items/{segment(item_id)}/attachments/{segment(attachment_id)}"
        try:
            response = self.client.delete(resource_path, params=params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def put_item_location(
        self,
        item_id: int,
        location: dict,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update the location of the item with the specified ID. The server
        only supports moving items between projects: a parent in the item's
        own project, whether an item or the project, is refused with a 400
        ("only supports moving items between projects"). To move items within
        a project use put_items_tree_location.

        Args:
            item_id: the API ID of the item to move
            location: the new parent, a dict with a key of "item" or "project"
                and the ID of the parent as the value, e.g. {"project": 1}

        Returns: The response status code.

        """
        body = {"parent": location}
        resource_path = f"items/{segment(item_id)}/location"
        try:
            response = self.client.put(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def put_items_tree_location(
        self,
        item_ids: list[int],
        parent_item_id: int,
        insert_before_item_id: int | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Move items under a parent item.

        Args:
            item_ids: the API IDs of the items to move
            parent_item_id: the API ID of the new parent item
            insert_before_item_id: optional API ID of a child of the new
                parent that the moved items are placed before. A batch of
                several items is placed in reverse order.

        Returns: The response status code.

        """
        body = {"itemIds": item_ids, "parentItemId": parent_item_id}
        if insert_before_item_id is not None:
            body["insertBeforeItemId"] = insert_before_item_id
        resource_path = f"{self.resource_path}/treeLocation"
        try:
            response = self.client.put(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def post_item_duplicate(
        self,
        item_id: int,
        include_tags: bool = False,
        include_attachments: bool = False,
        include_links: bool = False,
        *,
        params: dict | None = None,
        include_all_fields: bool | None = None,
        include_categories: bool | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a duplicate of the item with the specified ID. The name and
        description are copied and the name becomes "Duplicate of <name>".
        An item with children cannot be duplicated: the server answers 500, so
        the caller gets an APIServerException.

        Args:
            item_id: the API ID of the item to duplicate
            include_tags: copy the item's tags to the duplicate
            include_attachments: copy the item's attachments to the duplicate
            include_links: copy the item's links to the duplicate
            include_all_fields: copy all fields, not only name and description;
                left out of the request when None
            include_categories: copy the item's categories to the duplicate;
                left out of the request when None

        Returns: the client response; meta["id"] is the ID of the duplicate.

        """
        body = {
            "includeTags": include_tags,
            "includeAttachments": include_attachments,
            "includeLinks": include_links,
        }
        if include_all_fields is not None:
            body["includeAllFields"] = include_all_fields
        if include_categories is not None:
            body["includeCategories"] = include_categories
        resource_path = f"items/{segment(item_id)}/duplicate"
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def patch_items(
        self,
        patches: list[dict],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Apply patch operations to several items in one asynchronous request;
        a 200 means the work was accepted, so the change may not be visible
        immediately.

        Args:
            patches: A list of dicts, each naming the item IDs and the patch
                operations to apply to all of them (the body shape is
                undocumented; this is the shape the server accepts)
             [
                {
                    "items": [int],
                    "operations": [
                        {"op": string, "path": string, "value": {}}
                    ]
                }
            ]

        Returns: The response status code.

        """
        try:
            response = self.client.patch(
                self.resource_path, params, json=patches, **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def post_item_workflow_transition(
        self,
        item_id: int,
        transition_id: str,
        comment: str | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Execute a workflow transition on the item with the specified ID. Valid
        transitions are listed by get_item_workflow_transitions.

        Args:
            item_id: the API ID of the item
            transition_id: the ID of the transition to execute
            comment: optional comment recorded with the transition

        Returns: the client response

        """
        body = {"transitionId": transition_id}
        if comment is not None:
            body["comment"] = comment
        resource_path = f"items/{segment(item_id)}/workflowtransitions"
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_links(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all URL links on the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item
            allowed_results_per_page: number of results per page

        Returns: the client response, whose data is the list of links
        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/links"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_link(
        self,
        item_id: int,
        link_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Get a single link on the item with the specified ID

        Args:
            include: links to include as full objects in the linked map
            item_id: the API ID of the item
            link_id: the API ID of the link

        Returns: the client response
        """
        params = with_include(params, include)
        resource_path = f"items/{segment(item_id)}/links/{segment(link_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_item_link(
        self,
        item_id: int,
        url: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a URL link on the item with the specified ID

        Args:
            item_id: the API ID of the item
            url: the URL the link points to
            description: the text shown for the link

        Returns: the client response; meta["id"] is the ID of the new link.
        """
        body = {"url": url, "description": description}
        resource_path = f"items/{segment(item_id)}/links"
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_item_link(
        self,
        item_id: int,
        link_id: int,
        url: str,
        description: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update a URL link on the item with the specified ID. Both fields are
        sent, so both are replaced.

        Args:
            item_id: the API ID of the item
            link_id: the API ID of the link
            url: the URL the link points to
            description: the text shown for the link

        Returns: The response status code.
        """
        body = {"url": url, "description": description}
        resource_path = f"items/{segment(item_id)}/links/{segment(link_id)}"
        try:
            response = self.client.put(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_item_link(
        self,
        item_id: int,
        link_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Delete a link from the item with the specified ID

        Args:
            item_id: the API ID of the item
            link_id: the API ID of the link

        Returns: The response status code.
        """
        resource_path = f"items/{segment(item_id)}/links/{segment(link_id)}"
        try:
            response = self.client.delete(resource_path, params=params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_item_categories(
        self,
        item_id: int,
        *,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all categories applied to the item with the specified ID

        Args:
            item_id: the API ID of the item
            allowed_results_per_page: number of results per page

        Returns: the client response, whose data is the list of applied
            categories (categoryPathId, categoryPathName, ...)
        """
        resource_path = f"items/{segment(item_id)}/categories"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_item_categories(
        self,
        item_id: int,
        category_path_ids: list[int],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Apply categories to the item with the specified ID

        Args:
            item_id: the API ID of the item
            category_path_ids: the IDs of the category paths to apply

        Returns: The response status code.
        """
        body = {"categoryPathIds": category_path_ids}
        resource_path = f"items/{segment(item_id)}/categories"
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_item_categories(
        self,
        item_id: int,
        category_path_ids: list[int],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Unapply categories from the item with the specified ID. The category
        path IDs travel in a JSON request body of the DELETE.

        Args:
            item_id: the API ID of the item
            category_path_ids: the IDs of the category paths to unapply

        Returns: The response status code.
        """
        body = {"categoryPathIds": category_path_ids}
        resource_path = f"items/{segment(item_id)}/categories"
        try:
            response = self.client.delete_with_body(
                resource_path, body, params=params, **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_item_baselined_categories(
        self,
        item_id: int,
        baseline_id: int,
        *,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the categories of the item as they were in the specified baseline

        Args:
            item_id: the API ID of the item
            baseline_id: the API ID of the baseline
            allowed_results_per_page: number of results per page

        Returns: the client response, whose data is the list of categories
        """
        resource_path = f"items/{segment(item_id)}/baselinedcategories"
        return self.client.get_all(
            resource_path,
            {**(params or {}), "baselineId": baseline_id},
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_item_versioned_categories(
        self,
        item_id: int,
        version_number: int,
        *,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the categories applied to the item at the specified version.
        The server answers with a list of categories (categoryPathName,
        itemVersionIdApplied, ...), not the item object its docs show.

        Args:
            item_id: the API ID of the item
            version_number: the version number of the item
            allowed_results_per_page: number of results per page

        Returns: the client response, whose data is the list of categories
        """
        resource_path = f"items/{segment(item_id)}/versionedcategories"
        return self.client.get_all(
            resource_path,
            {**(params or {}), "versionNumber": version_number},
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )
