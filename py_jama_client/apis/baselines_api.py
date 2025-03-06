"""
Baselines API module

Example usage:
    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> baselines_api = BaselinesAPI(client)
    >>> baselines = baselines_api.get_baselines(project_id=82)
"""

import json
import logging
from typing import Optional

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
        *args,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        params: Optional[dict] = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Get all baselines in the project with the specified ID
        GET: /baselines/
        Args:
            project_id:  project resource id
        """
        req_params = {"project": project_id}
        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_baseline(
        self,
        baseline_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the baseline with the specified ID
        GET: /baselines/{baselineId}/

        Args:
            baseline_id: the id of the baseline to fetch
        """
        resource_path = f"{self.resource_path}/{baseline_id}"

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
        baseline_origin_id: str,
        name: str,
        description: str,
        baseline_status_pick_list_option: int,
        *args,
        **kwargs,
    ):
        """
        Update the baseline with the specified ID
        PUT: /baselines/{baselineId}/

        Args:
            baseline_id: baseline resource id
        """
        resource_path = f"{self.resource_path}/{baseline_id}"
        body = {
            "source": source,
            "baselineOriginType": baseline_origin_type,
            "baselineOriginId": baseline_origin_id,
            "name": name,
            "description": description,
            "baselineStatusPickListOption": baseline_status_pick_list_option,
        }
        try:
            response = self.client.put(resource_path, data=json.dumps(body) ** kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def delete_baseline(
        self,
        baseline_id: int,
        *args,
        **kwargs,
    ):
        """
        Delete the baseline with the specified ID
        DELETE: /baselines/{baselineId}

        Args:
            baseline_id: baseline resource id
        """
        resource_path = f"{self.resource_path}/{baseline_id}"
        try:
            response = self.client.delete(resource_path, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
            return JamaClient.handle_response_status(response)

    def get_baseline_review_link(
        self,
        baseline_id: int,
        *args,
        **kwargs,
    ):
        """
        Get related review link
        GET: /baselines/{baselineId}/reviewlink

        Args:
            baseline_id: baseline resource id
        """
        resource_path = f"{self.resource_path}/{baseline_id}/reviewlink"
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
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all baseline items in a baseline with the specified ID
        Args:
            baseline_id:  baseline resource id
        """
        resource_path = f"baselines/{baseline_id}/versioneditems"
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
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the baseline item with the specified ID in a baseline with the
        specified ID
        GET: /baselines/{baselineId}/versioneditems/{itemId}

        Args:
            baseline_id: baseline resource id
            item_id: baseline item resource id
        """
        resource_path = f"{self.resource_path}/{baseline_id}/versioneditems/{item_id}"
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
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all versioned relationships for the item in the baseline
        GET:
         /baselines/{baselineId}/versioneditems/{itemId}/versionedrelationships

        Args:
            baseline_id: baseline resource id
            item_id: baseline item resource id
        """
        resource_path = (
            f"{self.resource_path}/{baseline_id}/versioneditems/"
            f"{item_id}/versionedrelationships"
        )
        return self.client.get_all(
            resource_path, params, allowed_results_per_page, **kwargs
        )
