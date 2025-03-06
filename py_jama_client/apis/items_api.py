"""
Items API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> items_api = ItemsAPI(client)
    >>> items = items_api.get_items(project_id=1)
"""

import json
import logging
from typing import Optional

from py_jama_client.client import ClientResponse, JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException

py_jama_client_logger = logging.getLogger("py_jama_client")


class ItemsAPI:
    client: JamaClient

    resource_path = "items"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_items(
        self,
        project_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all items in the specified project.
        Args:
            project_id: the project ID
            allowed_results_per_page: number of results per page

        Returns: a Json array of item objects

        """

        req_params = {"project": project_id}
        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.client.get_all(
            self.resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_item(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return a singular item of a specified item id
        Args:
            item_id: the item id of the item to fetch

        Returns: a dictonary object representing the item

        """
        resource_path = f"{self.resource_path}/{item_id}"
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
        global_id: int = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will post a new item to Jama Connect.

        Args:
            project_id: (int) id of project
            item_type_id: (int) ID of an Item Type.
            child_item_type_id: (int) integer ID of an Item Type.
            location: (dict) containing key "parent"
            fields: (dict) dictionary item field data.
        Returns:
            newly created item

        "location": {
            "parent": {
            "item": 0,
                "project": 0
            }
        }
        """

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

        headers = {"content-type": "application/json"}
        try:
            response = self.client.post(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
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
        *args,
        params: Optional[dict] = None,
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
        resource_path = f"{self.resource_path}/{item_id}/tags"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.post(
                resource_path, params, data=json.dumps(body), headers=headers, **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def post_item_sync(
        self,
        source_item: int,
        pool_item: int,
        *args,
        params: Optional[dict],
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

        resource_path = f"{self.resource_path}/{pool_item}/synceditems"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.post(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
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
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ) -> int:
        """
        Add an existing attachment to the item with the specified ID
        :param item_id: this is the ID of the item
        :param attachment_id: The ID of the attachment
        :return: 201 if successful / the response status of the post operation
        """
        body = {"attachment": attachment_id}
        resource_path = f"items/{item_id}/attachments"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.post(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
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
        *args,
        params: Optional[dict] = None,
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
        resource_path = f"items/{item_id}"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        self.handle_response_status(response)
        return response.status_code

    def patch_item(
        self,
        item_id: int,
        patches: list[dict],
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ) -> int:
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

        Returns: The response status code

        """
        resource_path = f"items/{item_id}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            response = self.client.patch(
                resource_path,
                params,
                data=json.dumps(patches),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))

        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_item(
        self,
        item_id: int,
        *args,
        **kwargs,
    ) -> int:
        """
        This method will delete an item in Jama Connect.

        Args:
            item_id: The jama connect API ID of the item to be deleted

        Returns: The success status code.
        """
        resource_path = f"items/{item_id}"
        try:
            response = self.client.delete(resource_path)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_tagged_items(
        self,
        tag_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all items tagged with the specified ID

        Args:
            tag_id: The ID of the tag to fetch the results for.
            allowed_results_per_page: Number of results per page

        Returns:
            A List of items that match the tag.

        """
        resource_path = f"tags/{tag_id}/items"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_upstream_relationships(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the upstream relationships for the item with the
        specified API ID.
        Args:
            item_id: the api id of the item
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the upstream
        relationships for the item.

        """
        resource_path = "items/" + str(item_id) + "/upstreamrelationships"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_downstream_related(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the downstream related items for the item with
        the specified API ID.

        Args:
            item_id: the api id of the item to fetch downstream items for
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the downstream
        related items for the specified item.

        """
        resource_path = f"items/{item_id}/downstreamrelated"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_downstream_relationships(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the downstream relationships for the item with
        the specified API ID.

        Args:
            item_id: the api id of the item

        Returns: an array of dictionary objects that represent the downstream
        relationships for the item.

        """
        resource_path = f"items/{item_id}/downstreamrelationships"
        return self.client.get_all(
            resource_path, allowed_results_per_page=allowed_results_per_page
        )

    def get_items_upstream_related(
        self, item_id: int, *args, params: Optional[dict] = None, **kwargs
    ):
        """
        Returns a list of all the upstream related items for the item with the
        specified API ID.

        Args:
            item_id: the api id of the item to fetch upstream items for

        Returns: an array of dictionary objects that represent the upstream
        related items for the specified item.

        """
        resource_path = f"items/{item_id}/upstreamrelated"
        return self.client.get_all(resource_path, params, **kwargs)

    def get_item_workflow_transitions(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all valid workflow transitions that can be made with the specified
        API ID

        Args:
            item_id: the api id of the item
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the workflow
        transitions for the item.

        """
        resource_path = f"items/{item_id}/workflowtransitionoptions"
        return self.client.get_all(resource_path, params, **kwargs)

    def get_item_children(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return list of the child items of the item passed to
        the function.
        Args:
            item_id: (int) The id of the item for which children items should
            be fetched allowed_results_per_page: Number of results per page

        Returns: a List of Objects that represent the children of the item
        passed in.
        """
        resource_path = f"items/{item_id}/children"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_items_synceditems(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all synchronized items for the item with the specified ID

        Args:
            item_id: The API id of the item being
            allowed_results_per_page: Number of results per page

        Returns: A list of JSON Objects representing the items that are in the
        same synchronization group as the specified item.

        """
        resource_path = f"items/{item_id}/synceditems"
        return self.client.get_all(
            resource_path, allowed_results_per_page=allowed_results_per_page
        )

    def get_items_synceditems_status(
        self,
        item_id: int,
        synced_item_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the sync status for the synced item with the specified ID

        Args:
            item_id: The id of the item to compare against
            synced_item_id: the id of the item to check if it is in sync

        Returns: The response JSON from the API which contains a single field
            'inSync' with a boolean value.

        """
        resource_path = f"items/{item_id}/synceditems/{synced_item_id}/syncstatus"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_versions(
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
        resource_path = f"items/{item_id}/versions"
        return self.client.get_all(resource_path, params)

    def get_item_version(
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
        resource_path = f"items/{item_id}/versions/{version_num}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_versioned_item(
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
        resource_path = f"items/{item_id}/versions/{version_num}/versioneditem"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_versions(  # noqa: F811
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID

        Args:
            item_id: the item id of the item to fetch
            allowed_results_per_page: number of results per page

        Returns: JSON array with all versions for the item
        """
        resource_path = f"items/{item_id}/versions"
        return self.client.get_all(
            resource_path, params, allowed_results_per_page=allowed_results_per_page
        )

    def get_item_version(  # noqa F811
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
        resource_path = f"items/{item_id}/versions/{version_num}"
        response = self.client.get(resource_path, params)
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_versioned_item(  # noqa: F811
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
        resource_path = f"items/{item_id}/versions/{version_num}/versioneditem"
        response = self.client.get(resource_path, params)
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_lock(self, item_id: int, params: Optional[dict] = None):
        """
        Get the locked state, last locked date, and last locked by user for
        the item with the specified ID
        Args:
            item_id: The API ID of the item to get the lock info for.

        Returns:
            A JSON object with the lock information for the item with the
            specified ID.

        """
        resource_path = f"items/{item_id}/lock"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_item_lock(self, item_id: int, locked: bool) -> int:
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
        resource_path = f"items/{item_id}/lock"
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path,
                data=json.dumps(body),
                headers=headers,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        return self.handle_response_status(response)

    def get_item_tags(
        self,
        item_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Return all tags for the item with the specified ID

        Args:
            item_id: the item id of the item to fetch
            allowed_results_per_page: number of results

        Returns: a dictionary object representing the item's tags

        """
        resource_path = f"items/{item_id}/tags"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
        )
