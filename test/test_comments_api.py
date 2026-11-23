from unittest.mock import Mock

import pytest

from py_jama_client.apis.comments_api import CommentsAPI
from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
    UnauthorizedException,
)

MISSING_ID = 2147483647
UNREADABLE_COMMENT_ID = 31607


@pytest.fixture(scope="function")
def comments_api(get_test_jama_client):
    return CommentsAPI(get_test_jama_client)


def test_get_comment(comments_api, real_comment):
    comment = comments_api.get_comment(real_comment).data
    assert comment["id"] == real_comment
    assert isinstance(comment["body"]["text"], str)
    assert "item" in comment["location"]
    assert comment["commentType"]
    assert comment["status"]
    assert "inReplyTo" not in comment


def test_get_comment_missing(comments_api):
    with pytest.raises(ResourceNotFoundException):
        comments_api.get_comment(MISSING_ID)


def test_get_comment_unreadable_is_unauthorized(comments_api):
    # Default 31607 is a MOCK comment the API user cannot read (401).
    with pytest.raises(UnauthorizedException):
        comments_api.get_comment(UNREADABLE_COMMENT_ID)


def test_get_comment_replies(comments_api, real_comment):
    replies = comments_api.get_comment_replies(real_comment).data
    assert replies
    assert all(reply["inReplyTo"] == real_comment for reply in replies)
    assert all({"id", "body", "commentType", "createdBy"} <= set(r) for r in replies)
    # A reply takes its parent's location and does not repeat it.
    assert all("location" not in reply for reply in replies)


def test_get_item_comments(get_test_jama_client, resolved):
    item_id = resolved("real_commented_item")
    comments = ItemsAPI(get_test_jama_client).get_item_comments(item_id).data
    assert comments
    assert all(c["type"] == "comments" for c in comments)
    assert all(c["location"] == {"item": item_id} for c in comments)
    # Only top-level comments are listed; the fixture comment's reply comes
    # from get_comment_replies.
    assert all("inReplyTo" not in c for c in comments)


def test_post_comment(comments_api, resolved):
    # Creates a MockComment<N> comment, which the API cannot delete.
    item_id = resolved("real_commented_item")
    text = resolved("scratch_comment_text")
    response = comments_api.post_comment({"item": item_id}, text)
    assert response.meta["status"] == "Created"
    assert response.meta["location"].endswith(f"/comments/{response.meta['id']}")
    comment = comments_api.get_comment(response.meta["id"]).data
    assert comment["body"]["text"] == text
    assert comment["location"] == {"item": item_id}
    assert comment["commentType"] == "GENERAL"


def test_post_comment_reply(comments_api, resolved):
    # Creates a MockComment<N> reply, which the API cannot delete.
    parent = resolved("real_item_comment")
    text = resolved("scratch_reply_text")
    response = comments_api.post_comment(None, text, in_reply_to=parent)
    assert response.meta["status"] == "Created"
    reply = comments_api.get_comment(response.meta["id"]).data
    assert reply["body"]["text"] == text
    assert reply["inReplyTo"] == parent
    assert "location" not in reply


def test_get_comments_synthetic(comments_api):
    response = comments_api.get_comments(
        params={"rootCommentsOnly": True}, allowed_results_per_page=2
    )
    assert [comment["id"] for comment in response.data] == [201, 203, 204]
    assert {comment["location"]["project"] for comment in response.data} == {7}
    assert response.data[0]["body"] == {"text": "Comment text 1"}
    assert response.meta["pageInfo"]["totalResults"] == 3


def offline_api(status_code=200):
    client = Mock()
    for verb in ("get", "post"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text="",
        )
    client.get_all.return_value = Mock()
    return CommentsAPI(client), client


def test_post_comment_sends_json_body():
    api, client = offline_api(201)
    params = {"a": 1}
    location = {"item": 5}
    api.post_comment(location, "text", params=params, timeout=3)
    client.post.assert_called_once_with(
        "comments",
        params,
        json={
            "body": {"text": "text"},
            "location": {"item": 5},
            "commentType": "GENERAL",
        },
        timeout=3,
    )
    assert params == {"a": 1}
    assert location == {"item": 5}


def test_post_comment_reply_includes_in_reply_to():
    api, client = offline_api(201)
    api.post_comment({"item": 5}, "text", "REVIEW", in_reply_to=9)
    assert client.post.call_args.kwargs["json"] == {
        "body": {"text": "text"},
        "location": {"item": 5},
        "commentType": "REVIEW",
        "inReplyTo": 9,
    }


def test_post_comment_reply_without_location_inherits_the_parents():
    api, client = offline_api(201)
    api.post_comment(None, "text", in_reply_to=9)
    assert client.post.call_args.kwargs["json"] == {
        "body": {"text": "text"},
        "commentType": "GENERAL",
        "inReplyTo": 9,
    }


def test_post_comment_without_location_must_be_a_reply():
    api, client = offline_api(201)
    with pytest.raises(ValueError, match="exactly"):
        api.post_comment(None, "text")
    client.post.assert_not_called()


def test_post_comment_project_location():
    api, client = offline_api(201)
    api.post_comment({"project": 7}, "text")
    assert client.post.call_args.kwargs["json"]["location"] == {"project": 7}
    assert "inReplyTo" not in client.post.call_args.kwargs["json"]


@pytest.mark.parametrize(
    "location",
    [
        {"item": 5, "project": 7},
        {},
        {"item": None},
        {"project": None},
        {"item": 5, "extra": 1},
        {"item": True},
        {"extra": 1},
    ],
)
def test_post_comment_location_must_name_exactly_one(location):
    api, client = offline_api(201)
    with pytest.raises(ValueError, match="exactly"):
        api.post_comment(location, "text")
    client.post.assert_not_called()


def test_get_comment_passes_params_and_kwargs():
    api, client = offline_api()
    params = {"include": "createdBy"}
    api.get_comment(5, params=params, timeout=3)
    client.get.assert_called_once_with("comments/5", params, timeout=3)
    assert params == {"include": "createdBy"}


def test_list_methods_use_get_all_with_paging_and_kwargs():
    api, client = offline_api()
    params = {"rootCommentsOnly": True}
    api.get_comments(params=params, allowed_results_per_page=7, timeout=3)
    client.get_all.assert_called_with(
        "comments", params=params, allowed_results_per_page=7, timeout=3
    )
    api.get_comment_replies(5, params=params, allowed_results_per_page=7, timeout=3)
    client.get_all.assert_called_with(
        "comments/5/replies", params=params, allowed_results_per_page=7, timeout=3
    )
    items_api = ItemsAPI(client)
    items_api.get_item_comments(5, params=params, allowed_results_per_page=7, timeout=3)
    client.get_all.assert_called_with(
        "items/5/comments", params, allowed_results_per_page=7, timeout=3
    )
    assert params == {"rootCommentsOnly": True}


def test_core_exception_is_wrapped():
    api, client = offline_api()
    client.post.side_effect = CoreException("boom")
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException, match="boom"):
        api.post_comment({"item": 5}, "text")
    with pytest.raises(APIException, match="boom"):
        api.get_comment(5)


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_comments_maps_root_comments_only():
    api, client = offline_api()
    params = {"rootCommentsOnly": False}
    api.get_comments(params=params, root_comments_only=True)
    assert get_all_params(client) == {"rootCommentsOnly": True}
    assert params == {"rootCommentsOnly": False}
    api.get_comments()
    assert get_all_params(client) is None
