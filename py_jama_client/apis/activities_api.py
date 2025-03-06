"""
Activities API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> activities_api = ActivitiesAPI(client)
    >>> activities = activities_api.get_activities(project_id=82)
"""

import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class ActivitiesAPI:
    client: JamaClient

    resource_path = "activities"

    def __init__(self, client: JamaClient) -> None:
        self.client = client

    def get_activities(
        self,
        project_id: int,
        event_type: list[str] = None,
        object_type: list[str] = None,
        item_type: list[int] = None,
        date: list[str] = None,
        delete_events: bool = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all activities in the project with the specified ID
        GET /activities/

        Args:
            project_id: Project resource id
            event_type: Event type to filter on. More than one event type can
                be chosen
                Available values : CREATE, BATCH_CREATE, UPDATE, BATCH_UPDATE,
                DELETE, BATCH_DELETE, PUBLIC, BATCH_SUMMARY, COPY, BATCH_COPY,
                MOVE, APPLY, MERGE, CREATE_INSTANCE, EDIT, EDIT_PROJECT,
                REMOVE_INSTANCE, REMOVE
            object_type: Object type to filter on. More than one object type
                can be chosen
                Available values : PROJECT, ITEM, USER, RELATIONSHIP, COMMENT,
                ITEM_TAG, TAG, ITEM_ATTACHMENT, URL, TEST_RESULT, BASELINE,
                CHANGE_REQUEST, REVIEW, REVISION, REVISION_ITEM, TEST_PLAN,
                TEST_CYCLE, TEST_RUN, INTEGRATION, MISCELLANEOUS, CATEGORY,
                CATEGORIZED_ITEM, CATEGORY_PATH
            item_type: ID of item type to filter on. More than one item type
                can be chosen
            date: Filter datetime fields after a single date or within a range
                of values. Provide one or two values in ISO8601 format
                (milliseconds or seconds)
                - "yyyy-MM-dd'T'HH:mm:ss.SSSZ" or "yyyy-MM-dd'T'HH:mm:ssZ"
            delete_events: Get item delete events only
        """
        req_params = {"project": project_id}
        if params is None:
            params = req_params
        else:
            params.update(req_params)

        if event_type is not None:
            params.update({"objectType": object_type})
        if item_type is not None:
            params.update({"objectType": object_type})
        if date is not None:
            params.update({"date": date})
        if delete_events is not None:
            params.update({"delete": delete_events})

        return self.client.get_all(
            self.resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def get_activity(
        self,
        activity_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the activity with the specified ID
        GET /activities/{activityId}

        Args:
            activity_id: (int) activity resource id
        """
        resource_path = f"{self.resource_path}/{activity_id}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_activity_affected_items(
        self,
        activity_id: int,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all items affected by the activity with the specified ID
        GET: /activities/{activityId}/affecteditems

        Args:
            activity_id: (int) activity resource id
        """
        resource_path = f"{self.resource_path}/{activity_id}/affecteditems"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )

    def restore_activity_items(
        self,
        activity_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Restore item(s) associated with a delete activity.
        POST: /activities/{activityId}/restore

        Args:
            activity_id: (int) activity resource id
        """
        resource_path = f"{self.resource_path}/activities/{activity_id}/restore"
        try:
            response = self.client.post(
                resource_path,
                params,
                **kwargs,
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_admin_activities(
        self,
        filter_term: str = None,
        project_id: int = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all activities at the admin level
        GET: /activities/adminActivity

        Args:
            filter_term: (str) Filter on the text contents of the activities.
                         - Strings in quotations taken literally.
                         - Multiple values are treated as separate tokens
                                for matching.
            project_id: (int) Filter by Project ID. User must be at least
                        Project Administrator
        """
        if params is None:
            params = {}
        if filter_term is not None:
            params.update({"filterTerm": filter_term})
        if project_id is not None:
            params.update({"projectId": project_id})

        resource_path = f"{self.resource_path}/adminActivity"
        return self.client.get_all(
            resource_path,
            params,
            allowed_results_per_page,
            **kwargs,
        )
