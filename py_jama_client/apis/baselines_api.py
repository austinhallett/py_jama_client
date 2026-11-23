"""
Baselines API module

Example usage:
    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> baselines_api = BaselinesAPI(client)
    >>> baselines = baselines_api.get_baselines(project_id=82)
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class BaselinesAPI:
    client: JamaClient

    resource_path = "baselines"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_baselines(
        self,
        project_id: int,
        *,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        params: dict | None = None,
        include: list[str] | None = None,
        source: int | None = None,
        created_by: int | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Get all baselines in the project with the specified ID
        GET: /baselines/
        Args:
            include: links to include as full objects in the linked map
            project_id:  project resource id
            source: only baselines created from the baseline source (such as a
                release or filter) with this API ID (sent as source)
            created_by: only baselines created by the user with this API ID
                (sent as createdBy)
            Each of these overrides the same key in params.
        """
        params = with_include(params, include)
        params = {**(params or {}), "project": project_id}
        params = with_query(params, source=source, createdBy=created_by)

        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_baseline(
        self,
        baseline_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the baseline with the specified ID
        GET: /baselines/{baselineId}/

        Args:
            include: links to include as full objects in the linked map
            baseline_id: the id of the baseline to fetch
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(baseline_id)}"

        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_baseline(
        self,
        baseline_id: int,
        source: int,
        baseline_origin_type: str,
        baseline_origin_id: int,
        name: str,
        description: str,
        baseline_status_pick_list_option: int | None = None,
        **kwargs,
    ):
        """
        Update the baseline with the specified ID
        PUT: /baselines/{baselineId}/

        Args:
            baseline_id: baseline resource id
            baseline_status_pick_list_option: optional baseline status pick
                list option id; None sends null, which the server accepts
        """
        resource_path = f"{self.resource_path}/{segment(baseline_id)}"
        body = {
            "source": source,
            "baselineOriginType": baseline_origin_type,
            "baselineOriginId": baseline_origin_id,
            "name": name,
            "description": description,
            "baselineStatusPickListOption": baseline_status_pick_list_option,
        }
        try:
            response = self.client.put(resource_path, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def delete_baseline(
        self,
        baseline_id: int,
        **kwargs,
    ):
        """
        Delete the baseline with the specified ID
        DELETE: /baselines/{baselineId}

        Args:
            baseline_id: baseline resource id
        """
        resource_path = f"{self.resource_path}/{segment(baseline_id)}"
        try:
            response = self.client.delete(resource_path, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        return JamaClient.handle_response_status(response)

    def get_baseline_review_link(
        self,
        baseline_id: int,
        **kwargs,
    ):
        """
        Get related review link
        GET: /baselines/{baselineId}/reviewlink

        Args:
            baseline_id: baseline resource id
        """
        resource_path = f"{self.resource_path}/{segment(baseline_id)}/reviewlink"
        try:
            response = self.client.get(resource_path, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_baseline_versioned_items(
        self,
        baseline_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        categories: bool | None = None,
        **kwargs,
    ):
        """
        Get all baseline items in a baseline with the specified ID
        Args:
            include: links to include as full objects in the linked map
            baseline_id:  baseline resource id
            categories: if True, return all categories applied at the time the
                baseline was created (sent as categories; overrides the same
                key in params)
        """
        params = with_include(params, include)
        params = with_query(params, categories=categories)
        resource_path = f"baselines/{segment(baseline_id)}/versioneditems"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_baseline_versioned_item(
        self,
        baseline_id: int,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the baseline item with the specified ID in a baseline with the
        specified ID
        GET: /baselines/{baselineId}/versioneditems/{itemId}

        Args:
            include: links to include as full objects in the linked map
            baseline_id: baseline resource id
            item_id: baseline item resource id
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(baseline_id)}/versioneditems/{segment(item_id)}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_baseline_versioned_item_relationships(
        self,
        baseline_id: int,
        item_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all versioned relationships for the item in the baseline
        GET:
         /baselines/{baselineId}/versioneditems/{itemId}/versionedrelationships

        Args:
            include: links to include as full objects in the linked map
            baseline_id: baseline resource id
            item_id: baseline item resource id
        """
        params = with_include(params, include)
        resource_path = (
            f"{self.resource_path}/{segment(baseline_id)}/versioneditems/"
            f"{segment(item_id)}/versionedrelationships"
        )
        return self.client.get_all(
            resource_path, params, allowed_results_per_page, **kwargs
        )
