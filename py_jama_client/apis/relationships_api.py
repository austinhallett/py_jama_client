"""
Relationships API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> relationships_api = RelationshipsAPI(client)
    >>> relationships = relationships_api.get_relationships(project_id=82)
"""

import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class RelationshipsAPI:
    client: JamaClient

    resource_path = "relationships"

    def __init__(self, client: JamaClient):
        self.client = client

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

        req_params = {"project": project_id}
        if params is None:
            params = req_params
        else:
            params.update(req_params)

        return self.client.get_all(
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
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
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
            relationship_type: Optional integer API id of the relationship
                type to create

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
            relationship_type: Optional integer API id of the relationship
                type to create
        """
        body = {"fromItem": from_item, "toItem": to_item}
        if relationship_type is not None:
            body["relationshipType"] = relationship_type
        resource_path = "relationships/{}".format(relationship_id)
        headers = {"content-type": "application/json"}
        try:
            response = self.client.put(
                resource_path, params, data=json.dumps(body), headers=headers, **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def delete_relationship(self, relationship_id: int) -> int:
        """
        Deletes a relationship with the specified relationship ID

        Args:
            relationship_id: the api project id of a relationship

        Returns: The success status code.

        """
        resource_path = f"relationships/{relationship_id}"
        try:
            response = self.client.delete(resource_path)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def delete_relationship_suspect(self, relationship_id: int) -> int:
        """
        Removes suspect status of a relationship with the
        specified relationship ID

        Args:
            relationship_id: the api project id of a relationship

        Returns: The success status code.

        """
        resource_path = f"relationships/{relationship_id}/suspect"
        try:
            response = self.client.delete(resource_path)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_relationship_rule_sets(self):
        """
        This method will return all relationship rule sets across all projects
        of the Jama Connect instance.

        Returns: An array of dictionary objects representing a rule set and
        its associated rules

        """
        resource_path = "relationshiprulesets/"
        return self.client.get_all(resource_path)

    def get_relationship_rule_set(self, relationship_id: int):
        """
        This method will return the relationship rule sets by id.

        Returns: A dictionary object representing a rule set and its
                 associated rules

        """
        resource_path = f"relationshiprulesets/{relationship_id}"
        response = self.client.get(resource_path)
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_relationship_types(
        self,
        *args,
        params: Optional[dict] = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        This method will return all relationship types of the across all
        projects of the Jama Connect instance.

        Args:
            allowed_results_per_page: Number of results per page

        Returns: An array of dictionary objects

        """
        resource_path = "relationshiptypes/"
        return self.client.get_all(
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
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
