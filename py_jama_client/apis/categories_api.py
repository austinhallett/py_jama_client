"""
Categories API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> categories_api = CategoriesAPI(client)
    >>> categories = categories_api.get_categories(params={"projectId": PROJECT_ID})
"""

import logging

from py_jama_client.apis._include import with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class CategoriesAPI:
    client: JamaClient

    resource_path = "categories"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_categories(
        self,
        *,
        params: dict | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        category_name: str | None = None,
        project_id: int | None = None,
        **kwargs,
    ):
        """
        Search category paths by name and/or project.

        Args:
            params: other query parameters
            allowed_results_per_page: number of results per page
            category_name: category path name to search for (categoryName);
                overrides params
            project_id: project to search in (projectId); overrides params

        Returns: the client response, whose data is the list of category paths
        """
        params = with_query(params, categoryName=category_name, projectId=project_id)
        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_category(
        self,
        path: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a category path from a string path. This is an instance
        administration operation.

        Args:
            path: the category path to create

        Returns: the client response; data is the ID of the new category
            path. This is the shape the REST docs show for this endpoint
            ({"data": id}), unlike other creates, which put the ID in
            meta["id"]; it is only covered by a synthetic cassette.
        """
        body = {"path": path}
        try:
            response = self.client.post(self.resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_category_visibility(
        self,
        category_path_id: int,
        project_ids: list[int],
        is_global: bool,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Update which projects can use a category path.

        Args:
            category_path_id: the API ID of the category path
            project_ids: the IDs of the projects the category is visible in
            is_global: whether the category is visible in every project

        Returns: The response status code.
        """
        body = {"projectIds": project_ids, "isGlobal": is_global}
        resource_path = f"{self.resource_path}/{segment(category_path_id)}/visibility"
        try:
            response = self.client.put(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_category(
        self,
        category_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Delete a category and all of its category paths. The server infers
        the owning project; organization administrators may delete any
        category, project administrators those owned by a project they
        administer. The category and its paths must not be applied to items.

        Args:
            category_id: the API ID of the category

        Returns: The response status code (204).
        """
        return self._status(
            self.client.delete, f"categories/{segment(category_id)}", params, **kwargs
        )

    def delete_category_path(
        self,
        category_path_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Delete a category path and its descendants. Permissions as for
        delete_category; the paths must not be applied to items.

        Args:
            category_path_id: the API ID of the category path

        Returns: The response status code (204).
        """
        return self._status(
            self.client.delete,
            f"categorypaths/{segment(category_path_id)}",
            params,
            **kwargs,
        )

    def copy_category_path(
        self,
        category_path_id: int,
        destination_parent_category_path_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Copy a category path and its descendants under another path; matching
        paths merge recursively.

        Args:
            category_path_id: the API ID of the category path to copy
            destination_parent_category_path_id: the API ID of the new parent

        Returns: the client response; the new path's ID is in meta.id
        """
        body = {"destinationParentCategoryPathId": destination_parent_category_path_id}
        resource_path = f"categorypaths/{segment(category_path_id)}/copy"
        try:
            response = self.client.post(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def move_category_path(
        self,
        category_path_id: int,
        destination_parent_category_path_id: int,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> int:
        """
        Move a category path and its descendants under another path; matching
        paths merge recursively. The server answers 409 when the path is
        already under that parent.

        Args:
            category_path_id: the API ID of the category path to move
            destination_parent_category_path_id: the API ID of the new parent

        Returns: The response status code (200).
        """
        params = dict(params or {})
        params["destinationParentCategoryPathId"] = destination_parent_category_path_id
        return self._status(
            self.client.put,
            f"categorypaths/{segment(category_path_id)}/move",
            params,
            **kwargs,
        )

    def _status(self, verb, resource_path: str, params: dict | None, **kwargs) -> int:
        try:
            response = verb(resource_path, params=params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code
