"""
Attachments API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> attachments_api = AttachmentsAPI(client)
    >>> attachments = attachments_api.get_attachment(attachment_id=10)
"""

import json
import logging
from typing import Optional

from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class AttachmentsAPI:
    client: JamaClient

    resource_path = "attachments"

    def __init__(self, client: JamaClient) -> None:
        self.client = client

    def get_attachment(
        self,
        attachment_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the attachment with the specified ID
        GET: /attachments/{attachmentId}/

        Args:
            attachment_id: the attachment id of the attachment to fetch
        """
        resource_path = f"{self.resource_path}/{attachment_id}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_attachment_file(
        self,
        attachment_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ) -> bytes:
        """
        Download attachment file from the attachment with the specified ID
        GET: /attachments/{attachmentId}/file/

        Args:
            attachment_id: attachment resource id
        """
        resource_path = "files"
        req_params = {"url": attachment_id}

        if params is None:
            params = req_params
        else:
            params.update(req_params)

        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
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
        Upload attachment file to the attachment with the specified ID
        PUT: /attachments/{attachmentId}/file

        Args:
            attachment_id: the integer ID of the attachment item to which we
                are uploading the file
            file_path: the file path of the file to be uploaded
        """
        resource_path = f"attachments/{attachment_id}/file"
        with open(file_path, "rb") as f:
            files = {"file": f}
            try:
                response = self.client.put(
                    resource_path,
                    params,
                    files=files,
                    **kwargs,
                )
            except CoreException as err:
                py_jama_client_logger.error(err)
                raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.status_code

    def get_attachment_lock(
        self,
        attachment_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the locked state, last locked date, and last locked by user for
        the item with the specified ID
        GET: /attachments/{attachmentId}/lock

        Args:
            attachment_id: attachment resource id
        """
        resource_path = f"{self.resource_path}/{attachment_id}/lock"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def put_attachment_lock(
        self,
        attachment_id: int,
        locked: bool,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Update the locked state of the item with the specified ID
        PUT: /attachments/{attachmentId}/lock

        Args:
            attachment_id: attachment resource id
            locked: (bool) locked state
        """
        resource_path = f"{self.resource_path}/{attachment_id}/lock"
        body = {"locked": locked}
        try:
            response = self.client.put(
                resource_path, params, data=json.dumps(body), **kwargs
            )
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_attachment_versions(
        self,
        attachment_id: int,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID
        GET: /attachments/{attachmentId}/versions/

        Args:
            attachment_id: attachment resource id
        """
        resource_path = f"{self.resource_path}/{attachment_id}/versions/"
        return self.client.get_all(
            resource_path, params, allowed_results_per_page, **kwargs
        )

    def get_attachment_version(
        self,
        attachment_id: int,
        version_num: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the numbered version for the item with the specified ID
        GET: /attachments/{attachmentId}/versions/{versionNum}
        """
        resource_path = f"{self.resource_path}/{attachment_id}/versions/{version_num}"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_attachment_version_item(
        self,
        attachment_id: int,
        version_num: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        Get the snapshot of the attachment at the specified version
        GET: /attachments/{attachmentId}/versions/{versionNum}/versionedItem
        """
        resource_path = (
            f"{self.resource_path}/{attachment_id}/versions/{version_num}/versionedItem"
        )
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
