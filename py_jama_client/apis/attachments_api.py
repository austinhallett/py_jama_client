"""
Attachments API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> attachments_api = AttachmentsAPI(client)
    >>> attachments = attachments_api.get_attachment(attachment_id=10)
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the attachment with the specified ID
        GET: /attachments/{attachmentId}/

        Args:
            include: links to include as full objects in the linked map
            attachment_id: the attachment id of the attachment to fetch
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(attachment_id)}"
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
        *,
        params: dict | None = None,
        **kwargs,
    ) -> bytes:
        """
        Download attachment file from the attachment with the specified ID
        GET: /attachments/{attachmentId}/file

        Args:
            attachment_id: attachment resource id
        """
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/file"

        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.content

    def get_file(
        self,
        url: str,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> bytes:
        """
        Download the attachment file at the specified Jama URL
        GET: /files?url={url}

        Args:
            url: the Jama URL of the file, e.g.
                https://<host>/attachment/{attachmentId}/{fileName}
        """
        params = {**(params or {}), "url": url}
        try:
            response = self.client.get("files", params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response.content

    def get_attachment_comments(
        self,
        attachment_id: int,
        *,
        params: dict | None = None,
        root_comments_only: bool | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all comments for the attachment with the specified ID
        GET: /attachments/{attachmentId}/comments

        Args:
            include: links to include as full objects in the linked map
            attachment_id: attachment resource id
            params: optional query parameters
            root_comments_only: if True, get only root comments, without their
                replies (sent as rootCommentsOnly; overrides the same key in
                params)
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of comments

        docs: https://rest.jamasoftware.com/#operation_getItemComments
        """
        params = with_include(params, include)
        params = with_query(params, rootCommentsOnly=root_comments_only)
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/comments"
        return self.client.get_all(
            resource_path,
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def put_attachments_file(
        self,
        attachment_id: int,
        file_path: str,
        *,
        params: dict | None = None,
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
        resource_path = f"attachments/{segment(attachment_id)}/file"
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the locked state, last locked date, and last locked by user for
        the item with the specified ID
        GET: /attachments/{attachmentId}/lock

        Args:
            include: links to include as full objects in the linked map
            attachment_id: attachment resource id
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/lock"
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
        *,
        params: dict | None = None,
        **kwargs,
    ):
        """
        Update the locked state of the item with the specified ID
        PUT: /attachments/{attachmentId}/lock

        Args:
            attachment_id: attachment resource id
            locked: (bool) locked state
        """
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/lock"
        body = {"locked": locked}
        try:
            response = self.client.put(resource_path, params, json=body, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)

    def get_attachment_versions(
        self,
        attachment_id: int,
        allowed_results_per_page: int = DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get all versions for the item with the specified ID
        GET: /attachments/{attachmentId}/versions/

        Args:
            include: links to include as full objects in the linked map
            attachment_id: attachment resource id
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/versions/"
        return self.client.get_all(
            resource_path, params, allowed_results_per_page, **kwargs
        )

    def get_attachment_version(
        self,
        attachment_id: int,
        version_num: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the numbered version for the item with the specified ID
        GET: /attachments/{attachmentId}/versions/{versionNum}
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/versions/{segment(version_num)}"
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
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ):
        """
        Get the snapshot of the attachment at the specified version
        GET: /attachments/{attachmentId}/versions/{versionNum}/versioneditem
        """
        params = with_include(params, include)
        resource_path = f"{self.resource_path}/{segment(attachment_id)}/versions/{segment(version_num)}/versioneditem"
        try:
            response = self.client.get(resource_path, params, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return ClientResponse.from_response(response)
