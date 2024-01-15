"""
Core Jama Connect API class

This module contains core classes for interacting with the Jama Connect API

Classes:
    Core: This is the base class
    AsyncCore: This class inherits the Core class using the httpx.AsyncClient class
"""
import json
import math
import urllib3
import httpx
import time
import logging
from py_jama_client.exceptions import UnauthorizedTokenException
from typing import Tuple
from abc import ABC, abstractmethod
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
    AlreadyExistsException,
    TooManyRequestsException,
    APIClientException,
    APIServerException,
    UnauthorizedException,
)
from py_jama_client.response import ClientResponse
from typing import Optional
from httpx import Response

__DEBUG__ = False

# disable warnings for ssl verification
urllib3.disable_warnings()

py_jama_client_logger = logging.getLogger("py_jama_rest_client")

DEFAULT_ALLOWED_RESULTS_PER_PAGE = 20  # Default is 20, Max is 50. if set to greater than 50, only 50 will items return.


class AbstractClient(ABC):
    """
    Abstract core class
    This class defines the interface required to satisfy the base requirements of the client core class
    """

    @abstractmethod
    def close(self) -> None:
        """
        Method to close underlying session
        """
        ...

    @abstractmethod
    def delete(self, resource: str, **kwargs):
        """
        This method will perform a delete operation on the specified resource
        """
        ...

    @abstractmethod
    def get(self, resource: str, params: dict = None, **kwargs):
        """
        This method will perform a get operation on the specified resource
        """
        ...

    @abstractmethod
    def patch(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """
        This method will perform a patch operation to the specified resource
        """
        ...

    @abstractmethod
    def post(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """
        This method will perform a post operation to the specified resource.
        """
        ...

    @abstractmethod
    def put(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """
        This method will perform a put operation to the specified resource
        """
        ...


# class AsyncCore(Core):
#     session_class = httpx.AsyncClient

#     async def close(self):
#         return await self.__session.aclose()


class BaseClient:
    """
    Base client class
    """

    session_class = httpx.Client

    def __init__(
        self,
        host: str,
        credentials: Tuple[str, str] = ("username|client_id", "password|client_secret"),
        api_version: str = "/rest/v1/",
        oauth: bool = False,
        verify: bool = True,
        timeout: int = 30,
    ):
        # Instance variables
        self.__api_version = api_version
        self.__host_name = host + self.__api_version
        self.__credentials = credentials
        self.__oauth = oauth
        self.__verify = verify
        self.__session = self.session_class(verify=verify, timeout=timeout)

        # Setup OAuth if needed.
        if self.__oauth:
            self.__token_host = host + "/rest/oauth/token"
            self.__token = None
            self.__get_fresh_token()

    def close(self) -> None:
        """Method to close underlying session"""
        self.__session.close()

    async def close(self) -> None:
        raise RuntimeError("await syntax not supported on sync core client class")

    def delete(self, resource: str, **kwargs):
        """This method will perform a delete operation on the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.delete(url, **kwargs)

        return self.__session.delete(url, auth=self.__credentials, **kwargs)

    def get(self, resource: str, params: dict = None, **kwargs):
        """This method will perform a get operation on the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.get(url, params=params, **kwargs)

        return self.__session.get(url, auth=self.__credentials, params=params, **kwargs)

    def patch(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a patch operation to the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.patch(
                url, params=params, data=data, json=json, **kwargs
            )

        return self.__session.patch(
            url, auth=self.__credentials, params=params, data=data, json=json, **kwargs
        )

    def post(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a post operation to the specified resource."""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.post(
                url, params=params, data=data, json=json, **kwargs
            )

        return self.__session.post(
            url, auth=self.__credentials, params=params, data=data, json=json, **kwargs
        )

    def put(self, resource: str, params: dict = None, data=None, json=None, **kwargs):
        """This method will perform a put operation to the specified resource"""
        url = self.__host_name + resource

        if self.__oauth:
            self.__check_oauth_token()
            kwargs["headers"] = self.__add_auth_header(**kwargs)
            return self.__session.put(
                url, data=data, params=params, json=json, **kwargs
            )

        return self.__session.put(
            url, auth=self.__credentials, data=data, params=params, json=json, **kwargs
        )

    def __check_oauth_token(self):
        if self.__token is None:
            self._get_fresh_token()

        else:
            time_elapsed = time.time() - self.__token_acquired_at
            time_remaining = self.__token_expires_in - time_elapsed
            if time_remaining < 60:
                # if less than a minute remains, just get another token.
                self.__get_fresh_token()

    def __get_fresh_token(self):
        """This method will fetch a new oauth bearer token from the oauth token server."""
        data = {"grant_type": "client_credentials"}

        # By getting the system time before we get the token we avoid a potential bug where the token may be expired.
        time_before_request = time.time()

        # Post to the token server, check if authorized
        try:
            response = httpx.post(
                self.__token_host,
                auth=self.__credentials,
                data=data,
                verify=self.__verify,
            )
            response.raise_for_status()
        except httpx.HTTPError as err:
            raise UnauthorizedTokenException(f"Unable to fetch token: {err}")

        # If success get relevant data
        if response.status_code in [200, 201]:
            response_json = response.json()
            self.__token = response_json["access_token"]
            self.__token_expires_in = response_json["expires_in"]
            self.__token_acquired_at = math.floor(time_before_request)

        else:
            py_jama_rest_client_logger.error("Failed to retrieve OAuth Token")

    def __add_auth_header(self, **kwargs):
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["Authorization"] = "Bearer " + self.__token
        return headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.__session.close()

    def get_all(
        self,
        resource,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will get all of the resources specified by the resource parameter, if an id or some other
        parameter is required for the resource, include it in the params parameter.
        Returns a single JSON array with all of the retrieved items.
        """

        if allowed_results_per_page < 1 or allowed_results_per_page > 50:
            raise ValueError("Allowed results per page must be between 1 and 50")

        start_index = 0
        allowed_results_per_page = 20
        total_results = float("inf")

        data, meta, links, linked = [], {}, {}, {}

        while len(data) < total_results:
            page = self.get_page(resource, start_index, params=params, **kwargs)

            meta.update(page.meta)
            links.update(page.links)
            linked.update(page.linked)

            page_info = page.meta.get("pageInfo")
            start_index = page_info.get("startIndex") + allowed_results_per_page
            total_results = page_info.get("totalResults")
            data.extend(page.data)

        return ClientResponse(meta, links, linked, data)

    def get_page(
        self,
        resource,
        start_at,
        params: dict = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return one page of results from the specified resource type.
        Pass any needed parameters along
        The response object will be returned
        """
        pagination = {"startAt": start_at, "maxResults": allowed_results_per_page}

        if params is None:
            params = pagination
        else:
            params.update(pagination)

        try:
            response = self.__session.get(resource, params=params, **kwargs)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    @staticmethod
    def handle_response_status(response: Response):
        """
        Utility method for checking http status codes.
        If the response code is not in the 200 range, An exception will be thrown.
        """

        status = response.status_code

        if status in range(200, 300):
            return status

        if status in range(400, 500):
            """These are client errors. It is likely that something is wrong with the request."""

            response_message = "No Response"

            try:
                response_json = json.loads(response.text)
                response_message = response_json.get("meta").get("message")

            except json.JSONDecodeError:
                pass

            # Log the error
            py_jama_rest_client_logger.error(
                "API Client Error. Status: {} Message: {}".format(
                    status, response_message
                )
            )

            if response_message is not None and "already exists" in response_message:
                raise AlreadyExistsException(
                    "Entity already exists.",
                    status_code=status,
                    reason=response_message,
                )

            if status == 401:
                raise UnauthorizedException(
                    "Unauthorized: check credentials and permissions.  "
                    "API response message {}".format(response_message),
                    status_code=status,
                    reason=response_message,
                )

            if status == 404:
                raise ResourceNotFoundException(
                    "Resource not found. check host url.",
                    status_code=status,
                    reason=response_message,
                )

            if status == 429:
                raise TooManyRequestsException(
                    "Too many requests.  API throttling limit reached, or system under "
                    "maintenance.",
                    status_code=status,
                    reason=response_message,
                )

            raise APIClientException(
                "{} {} Client Error.  Bad Request.  "
                "API response message: {}".format(
                    status, response.reason, response_message
                ),
                status_code=status,
                reason=response_message,
            )

        if status in range(500, 600):
            """These are server errors and network errors."""

            # Log The Error
            py_jama_rest_client_logger.error(
                "{} Server error. {}".format(status, response.reason)
            )
            raise APIServerException(
                "{} Server Error.".format(status),
                status_code=status,
                reason=response.reason,
            )

        # Catch anything unexpected
        py_jama_rest_client_logger.error("{} error. {}".format(status, response.reason))
        raise APIException(
            "{} error".format(status), status_code=status, reason=response.reason
        )


class JamaClient(BaseClient):
    """
    A class to abstract communication with the Jama Connect API
    """

    def get_available_endpoints(self):
        try:
            response = self.__session.get("")
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return response.json()["data"]

    def get_baselines(
        self,
        project_id: int,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
    ) -> ClientResponse:
        """
        Returns a list of Baseline objects
        Args:
            project_id:  the Id of the project to fetch baselines for
            allowed_results_per_page: number of results per page

        Returns: a list of Baseline objects
        """
        resource_path = "baselines"
        if params is not None:
            params.update({"project": project_id})
        else:
            params = {"project": project_id}

        return self.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_baseline(self, baseline_id: int, params: Optional[dict] = None):
        """
        Get baseline by id

        Args:
            baseline_id: the id of the baseline to fetch

        Returns:
            a dictionary object representing the baseline

        """
        resource_path = "baselines/" + str(baseline_id)

        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_baselines_versioneditems(
        self,
        baseline_id: int,
        params: Optional[dict] = None,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
    ):
        """
        Get all baseline items in a baseline with the specified ID
        Args:
            baseline_id:  The id of the baseline to fetch items for.
            allowed_results_per_page: Number of results per page
        Returns: A list of versioned items belonging to the baseline
        """
        resource_path = "baselines/" + str(baseline_id) + "/versioneditems"
        return self.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_filter_results(
        self,
        filter_id: int,
        project_id: int = None,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all results items for the filter with the specified ID

        Args:
            filter_id: The ID of the filter to fetch the results for.
            project_id: Use this only for filters that run on any project, where projectScope is CURRENT
            allowed_results_per_page: Number of results per page

        Returns:
            A List of items that match the filter.

        """
        resource_path = f"filters/{filter_id}/results"

        req_params = {"project": project_id}

        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_attachment(self, attachment_id: int, params: Optional[dict] = None):
        """
        This method will return a singular attachment of a specified attachment id
        Args:
            attachment_id: the attachment id of the attachment to fetch

        Returns: a dictonary object representing the attachment

        """
        resource_path = f"attachments/{attachment_id}"
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_relationship_rule_sets(self):
        """
        This method will return all relationship rule sets across all projects of the Jama Connect instance.

        Returns: An array of dictionary objects representing a rule set and its associated rules

        """
        resource_path = "relationshiprulesets/"
        return self.get_all(resource_path)

    def get_relationship_rule_set(self, id: int):
        """
        This method will return the relationship rule sets by id.

        Returns: A dictionary object representing a rule set and its associated rules

        """
        resource_path = f"relationshiprulesets/{id}"
        response = self._core.get(resource_path)
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_relationship_types(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all relationship types of the across all projects of the Jama Connect instance.

        Args:
            allowed_results_per_page: Number of results per page

        Returns: An array of dictionary objects

        """
        resource_path = "relationshiptypes/"
        return self.get_all(
            resource_path, allowed_results_per_page=allowed_results_per_page
        )

    def get_relationship_type(
        self, relationship_type_id: int, *args, params: Optional[dict] = None, **kwargs
    ):
        """
        Gets relationship type information for a specific relationship type id.

        Args:
            relationship_type_id: The api id of the item type to fetch

        Returns: JSON object

        """
        resource_path = f"relationshiptypes/{relationship_type_id}"
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_item_types(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all item types of the across all projects of the Jama Connect instance.

        Args:
            allowed_results_per_page: Number of results per page

        Returns: An array of dictionary objects

        """
        resource_path = "itemtypes/"
        return self.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_item_type(
        self,
        item_type_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets item type information for a specific item type id.

        Args:
            item_type_id: The api id of the item type to fetch

        Returns: JSON object

        """
        resource_path = f"itemtypes/{item_type_id}"
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_pick_lists(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all the pick lists

        Args:
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects

        """
        resource_path = "picklists/"
        return self.get_all(
            resource_path, params, allowed_results_per_page=allowed_results_per_page
        )

    def get_pick_list(
        self,
        pick_list_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Gets all a singular picklist

        Args:
            pick_list_id: The API id of the pick list to fetch

        Returns: a dictionary object representing the picklist.

        """
        resource_path = "picklists/" + str(pick_list_id)
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_pick_list_options(
        self,
        pick_list_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Gets all all the picklist options for a single picklist
        Args:
            pick_list_id: the api id of the picklist to fetch options for.
            allowed_results_per_page: number of results per page

        Returns: an array of dictionary objects that represent the picklist options.

        """
        resource_path = f"picklists/{pick_list_id}/options"
        return self.get_all(
            resource_path, params, allowed_results_per_page=allowed_results_per_page
        )

    def get_pick_list_option(
        self,
        pick_list_option_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Fetches a single picklist option from the API
        Args:
            pick_list_option_id: The API ID of the picklist option to fetch

        Returns: A dictonary object representing the picklist option.

        """
        resource_path = f"picklistoptions/{pick_list_option_id}"
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_relationships(
        self,
        project_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Returns a list of all relationships of a specified project

        Args:
            project_id: the api project id of a project
            allowed_results_per_page: number of results per page

        Returns: a list of dictionary objects that represents a relationships

        """
        resource_path = "relationships"
        if params is None:
            params = {"project": project_id}
        else:
            params.update({"project": project_id})

        return self.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
        )

    def get_relationship(
        self,
        relationship_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Returns a specific relationship object of a specified relationship ID

        Args:
            relationship_id: the api project id of a relationship

        Returns: a dictionary object that represents a relationship

        """
        resource_path = f"relationships/{relationship_id}"
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_items(
        self,
        project: list[int] = None,
        item_type: list[int] = None,
        document_key: list[str] = None,
        release: list[int] = None,
        created_date: list[str] = None,
        modified_date: list[str] = None,
        last_activity_date: list[str] = None,
        contains: list[str] = None,
        sort_by: list[str] = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return all items that match the query parameters entered.

        Args:
            project:            Array[integer]
            item_type:          Array[integer]
            document_key:       Array[string]
            release:            Array[integer]
            created_date:       Array[string]
            modified_date:      Array[string]
            last_activity_date: Array[string]
            contains:           Array[string]
            sort_by:            Array[string]

        Returns:
            A JSON Array of items.

        """
        resource_path = "abstractitems"

        # Add each parameter that is not null to the request.
        params = {}

        if project is not None:
            params["project"] = project

        if item_type is not None:
            params["itemType"] = item_type

        if document_key is not None:
            params["documentKey"] = document_key

        if release is not None:
            params["release"] = release

        if created_date is not None:
            params["createdDate"] = created_date

        if modified_date is not None:
            params["modifiedDate"] = modified_date

        if last_activity_date is not None:
            params["lastActivityDate"] = last_activity_date

        if contains is not None:
            params["contains"] = contains

        if sort_by is not None:
            params["sortBy"] = sort_by

        return self.get_all(resource_path, params, **kwargs)

    def get_abstract_item(
        self, item_id: int, *args, params: Optional[dict] = None, **kwargs
    ):
        """
        This method will return an item, test plan, test cycle, test run, or attachment with the specified ID
        Args:
            item_id: the item id of the item to fetch

        Returns: a dictonary object representing the abstract item

        """
        resource_path = f"abstractitems/{item_id}"
        try:
            response = self._core.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_item_versions(
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
        resource_path = f"abstractitems/{item_id}/versions"
        return self.get_all(resource_path, params, **kwargs)

    def get_abtract_item_version(
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
        resource_path = f"abstractitems/{item_id}/versions/{version_num}"
        try:
            response = self._core.get(resource_path, params)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_abstract_versioned_item(
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
        resource_path = f"abstractitems/{item_id}/versions/{version_num}/versioneditem"
        try:
            response = self._core.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_testruns(
        self,
        test_cycle_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all test runs associated with the specified test cycle.  Test runs will be returned
        as a list of json objects.
        Args:
            test_cycle_id: (int) The id of the test cycle
        """
        resource_path = f"testcycles/{test_cycle_id}/testruns"
        return self.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_tags(
        self,
        project_id: int,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all tags for the project with the specified id
        Args:
            project: The API ID of the project to fetch tags for.
            allowed_results_per_page: Number of results per page

        Returns: A Json Array that contains all the tag data for the specified project.

        """
        resource_path = "tags"
        project_param = {"project": project_id}
        if params is None:
            params = project_param
        else:
            params.update(project_param)
        return self.get_all(
            resource_path,
            params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def get_test_cycle(
        self,
        test_cycle_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return JSON data about the test cycle specified by the test cycle id.

        Args:
            test_cycle_id: the api id of the test cycle to fetch

        Returns: a dictionary object that represents the test cycle

        """
        resource_path = f"testcycles/{test_cycle_id}"
        try:
            response = self._core.get(resource_path)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def delete_relationships(self, relationship_id: int) -> int:
        """
        Deletes a relationship with the specified relationship ID

        Args:
            relationship_id: the api project id of a relationship

        Returns: The success status code.

        """
        resource_path = f"relationships/{relationship_id}"
        try:
            response = self._core.delete(resource_path)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return response.status_code

    def post_tag(
        self,
        name: str,
        project: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Create a new tag in the project with the specified ID
        Args:
            name: The display name for the tag
            project: The project to create the new tag in

        Returns: the newly created Tag
        """
        resource_path = "tags"
        body = {"name": name, "project": project}
        headers = {"content-type": "application/json"}
        try:
            response = self._core.post(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_testplans_testcycles(
        self,
        testplan_id: int,
        testcycle_name: str,
        start_date: str,
        end_date: str,
        testgroups_to_include: list[int] = None,
        testrun_status_to_include: list[str] = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will create a new Test Cycle.

        Args:
            testplan_id (int): The API_ID of the testplan to create the test cycle from.
            testcycle_name (str): The name you would like to set for the new Test Cycle
            start_date (str): Start date in 'yyyy-mm-dd' Format
            end_date (str): End date in 'yyyy-mm-dd' Format
            testgroups_to_include (int[]):  This array of integers specify the test groups to be included.
            testrun_status_to_include (str[]): Only valid after generating the first Test Cycle, you may choose to only
                generate Test Runs that were a specified status in the previous cycle. Do not specify anything to
                include all statuses

        Returns:
            (int): Returns the the newly created testcycle
        """
        resource_path = f"testplans/{testplan_id}/testcycles"
        headers = {"content-type": "application/json"}
        fields = {"name": testcycle_name, "startDate": start_date, "endDate": end_date}
        test_run_gen_config = {}
        if testgroups_to_include is not None:
            test_run_gen_config["testGroupsToInclude"] = testgroups_to_include
        if testrun_status_to_include is not None:
            test_run_gen_config["testRunStatusesToInclude"] = testrun_status_to_include
        body = {"fields": fields, "testRunGenerationConfig": test_run_gen_config}

        # Make the API Call
        try:
            response = self._core.post(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))

        # Validate response
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def post_relationship(
        self,
        from_item: int,
        to_item: int,
        relationship_type: int = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Args:
            from_item: integer API id of the source item
            to_item: integer API id of the target item
            relationship_type: Optional integer API id of the relationship type to create

        Returns: The integer ID of the newly created relationship.

        """
        body = {
            "fromItem": from_item,
            "toItem": to_item,
        }
        if relationship_type is not None:
            body["relationshipType"] = relationship_type
        resource_path = "relationships/"
        headers = {"content-type": "application/json"}
        try:
            response = self._core.post(
                resource_path,
                params,
                data=json.dumps(body),
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_relationship(
        self,
        relationship_id: int,
        from_item: int,
        to_item: int,
        relationship_type: int = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Args:
            relationship_id: integer API id of the relationship
            from_item: integer API id of the source item
            to_item: integer API id of the target item
            relationship_type: Optional integer API id of the relationship type to create
        """
        body = {"fromItem": from_item, "toItem": to_item}
        if relationship_type is not None:
            body["relationshipType"] = relationship_type
        resource_path = "relationships/{}".format(relationship_id)
        headers = {"content-type": "application/json"}
        try:
            response = self._core.put(
                resource_path, params, data=json.dumps(body), headers=headers, **kwargs
            )
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_attachment_file(
        self,
        attachment_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return a singular attachment of a specified attachment id
        Args:
            id: (int) attachment ID
        Returns:
            attachment bytes
        """
        resource_path = "files"
        req_params = {"url": attachment_id}

        if params is None:
            params = req_params
        else:
            params.update(req_params)

        try:
            response = self._core.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        self.handle_response_status(response)
        return response.content

    def put_attachments_file(
        self,
        attachment_id: int,
        file_path: str,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ) -> int:
        """
        Upload a file to a jama attachment
        :param attachment_id: the integer ID of the attachment item to which we are uploading the file
        :param file_path: the file path of the file to be uploaded
        :return: returns the status code of the call
        """
        resource_path = f"attachments/{attachment_id}/file"
        with open(file_path, "rb") as f:
            files = {"file": f}
            try:
                response = self._core.put(
                    resource_path,
                    params,
                    files=files,
                    **kwargs,
                )
            except CoreException as err:
                py_jama_rest_client_logger.error(err)
                raise APIException(str(err))
        self.handle_response_status(response)
        return response.status_code

    def put_test_run(
        self,
        test_run_id: int,
        data: dict = None,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """This method will post a test run to Jama through the API"""
        resource_path = f"testruns/{test_run_id}"
        headers = {"content-type": "application/json"}
        try:
            response = self._core.put(
                resource_path,
                params,
                data=data,
                headers=headers,
                **kwargs,
            )
        except CoreException as err:
            py_jama_rest_client_logger.error(err)
            raise APIException(str(err))
        self.handle_response_status(response)
        return response.status_code


def get_jama_client(*args, **kwargs) -> JamaClient:
    """
    Returns the global JamaClient instance.

    Returns:
        JamaClient: The global JamaClient instance.
    """
    return JamaClient(Core(*args, **kwargs))
