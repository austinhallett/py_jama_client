"""
Activities API module

Example usage:

    >>> from py_jama_rest_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> activities_api = ActivitiesAPI(client)
    >>> abstract_items = abstract_items_api.get_abstract_items()    
"""

import json
import logging
from typing import Optional
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.client import JamaClient
from py_jama_client.response import ClientResponse
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_client_logger = logging.getLogger("py_jama_rest_client")


class ActivitiesAPI:
    client: JamaClient

    resource_path = "activities"

    def get_activities(
        project_id: int,
        event_type: list[str] = None,
        object_type: list[str] = None,
        item_type: list[int] = None,
        date: list[str] = None,
        delete: bool = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all activities in the project with the specified ID

        Args:
            project_id: (int) project id
        """
        ...

    def get_activity(
        activity_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        ...

    def get_activity_affected_items(
        activity_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        ...

    def restore_activity_items(
        activity_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        ...

    def get_admin_activities(
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        ...
