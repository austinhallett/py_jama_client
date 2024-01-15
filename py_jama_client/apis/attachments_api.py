"""
Attachments API module

Example usage:

    >>> from py_jama_rest_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> attachments_api = AttachmentsAPI(client)
    >>> attachments = attachments_api.get_attachments()    
"""

import json
import logging
from typing import Optional
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.client import BaseClient
from py_jama_client.response import ClientResponse
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE

py_jama_client_logger = logging.getLogger("py_jama_rest_client")


class AttachmentsAPI:
    client: BaseClient

    resource_path = "users"

    def get_attachment(
        self,
        attachment_id: int,
        *args,
        params: Optional[dict] = None,
        **kwargs,
    ):
        """
        This method will return a singular attachment of a specified attachment id
        Args:
            attachment_id: the attachment id of the attachment to fetch

        Returns: a dictonary object representing the attachment

        """
        resource_path = f"attachments/{attachment_id}"
        try:
            response = self.client.get(resource_path, params)
        except CoreException as err:
            py_jama_client_logger.error(err)
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
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        BaseClient.handle_response_status(response)
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
                response = self.client.put(
                    resource_path,
                    params,
                    files=files,
                    **kwargs,
                )
            except CoreException as err:
                py_jama_client_logger.error(err)
                raise APIException(str(err))
        BaseClient.handle_response_status(response)
        return response.status_code
