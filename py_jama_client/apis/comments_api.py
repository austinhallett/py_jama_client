"""
Comments API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> comments_api = CommentsAPI(client)
    >>> comment_id = comments_api.post_comment({"item": ITEM_ID}, "text").meta["id"]
"""

import logging

from py_jama_client.apis._include import with_include, with_query
from py_jama_client.apis._path import segment
from py_jama_client.client import JamaClient
from py_jama_client.constants import DEFAULT_ALLOWED_RESULTS_PER_PAGE
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class CommentsAPI:
    client: JamaClient

    resource_path = "comments"

    def __init__(self, client: JamaClient):
        self.client = client

    def get_comments(
        self,
        *,
        params: dict | None = None,
        root_comments_only: bool | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get all comments viewable by the current user. This can be a very
        large listing; the only documented filter is rootCommentsOnly.

        Args:
            include: links to include as full objects in the linked map
            params: optional query parameters
            root_comments_only: if True, get only root comments, without their
                replies (sent as rootCommentsOnly; overrides the same key in
                params)
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of comments
        """
        params = with_include(params, include)
        params = with_query(params, rootCommentsOnly=root_comments_only)
        return self.client.get_all(
            "comments",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def post_comment(
        self,
        location: dict | None,
        text: str,
        comment_type: str = "GENERAL",
        in_reply_to: int | None = None,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Create a comment on an item or a project, or a reply to a comment.

        Args:
            location: where to comment; exactly one of {"item": item_id} or
                {"project": project_id}. A reply may pass None to take its
                parent's location (the server rejects any other location).
            text: The comment text
            comment_type: The comment type, default "GENERAL"
            in_reply_to: The API ID of the comment to reply to

        Returns: the client response; the new comment ID is in meta.id

        Raises:
            ValueError: if location is not exactly one of item or project with an
                integer ID, or is None for a comment that is not a reply
        """
        if location is None:
            if in_reply_to is None:
                raise ValueError(
                    'location must be exactly {"item": id} or {"project": id}; '
                    "only a reply may omit it"
                )
        elif (
            len(location) != 1
            or next(iter(location)) not in ("item", "project")
            or type(next(iter(location.values()))) is not int
        ):
            raise ValueError('location must be exactly {"item": id} or {"project": id}')
        body: dict = {"body": {"text": text}}
        if location is not None:
            body["location"] = dict(location)
        body["commentType"] = comment_type
        if in_reply_to is not None:
            body["inReplyTo"] = in_reply_to
        return ClientResponse.from_response(
            self._call(self.client.post, "comments", params, json=body, **kwargs)
        )

    def get_comment(
        self,
        comment_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Get a comment

        Args:
            include: links to include as full objects in the linked map
            comment_id: The API ID of the comment
            params: optional query parameters

        Returns: the client response, whose data is the comment
        """
        params = with_include(params, include)
        return ClientResponse.from_response(
            self._call(
                self.client.get, f"comments/{segment(comment_id)}", params, **kwargs
            )
        )

    def get_comment_replies(
        self,
        comment_id: int,
        *,
        params: dict | None = None,
        include: list[str] | None = None,
        allowed_results_per_page=DEFAULT_ALLOWED_RESULTS_PER_PAGE,
        **kwargs,
    ):
        """
        Get the replies to a comment

        Args:
            include: links to include as full objects in the linked map
            comment_id: The API ID of the comment
            params: optional query parameters
            allowed_results_per_page: Number of results per page

        Returns: the client response, whose data is the list of replies
        """
        params = with_include(params, include)
        return self.client.get_all(
            f"comments/{segment(comment_id)}/replies",
            params=params,
            allowed_results_per_page=allowed_results_per_page,
            **kwargs,
        )

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
