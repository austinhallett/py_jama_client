from unittest.mock import Mock

import pytest

from py_jama_client.apis.usergroups_api import UserGroupsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
    UnauthorizedException,
)

GROUP_KEYS = {"id", "uid", "name", "description", "project", "type"}


@pytest.fixture(scope="function")
def user_groups_api(get_test_jama_client):
    return UserGroupsAPI(get_test_jama_client)


def test_get_user_groups_docs(user_groups_api):
    response = user_groups_api.get_user_groups()
    assert [group["id"] for group in response.data] == [11, 12]
    assert all(GROUP_KEYS <= set(group) for group in response.data)
    assert {group["type"] for group in response.data} == {"usergroups"}


def test_post_user_group_docs(user_groups_api):
    # The docs give no example request body, only the RequestUserGroup model.
    response = user_groups_api.post_user_group(
        "Example group 1", "Example description 1", 7
    )
    assert response.meta["id"] == 101
    assert response.meta["location"].endswith("/usergroups/101")


def test_get_user_group_docs(user_groups_api):
    response = user_groups_api.get_user_group(11)
    assert response.data["id"] == 11
    assert GROUP_KEYS <= set(response.data)


def test_put_user_group_docs(user_groups_api):
    # The docs give no example request body, only the RequestUserGroup model.
    status = user_groups_api.put_user_group(
        11, "Example group 1", "Example description 1", 7
    )
    assert status == 200


def test_delete_user_group_docs(user_groups_api):
    assert user_groups_api.delete_user_group(11) == 204


def test_get_user_group_users_docs(user_groups_api):
    response = user_groups_api.get_user_group_users(11)
    assert [user["id"] for user in response.data] == [9, 10]
    assert all(
        {"id", "username", "firstName", "lastName", "licenseType"} <= set(user)
        for user in response.data
    )
    assert {user["type"] for user in response.data} == {"users"}


def test_post_user_group_user_docs(user_groups_api):
    # The docs give no example request body, only the RequestGroupUser model.
    response = user_groups_api.post_user_group_user(11, 9)
    assert response.meta["id"] == 9
    assert response.meta["location"].endswith("/usergroups/11/users/9")


def test_delete_user_group_user_docs(user_groups_api):
    assert user_groups_api.delete_user_group_user(11, 9) == 204


def offline_api():
    client = Mock()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
        )
    return UserGroupsAPI(client), client


def test_project_is_left_out_of_body_when_none():
    api, client = offline_api()
    api.post_user_group("a", "b")
    api.put_user_group(5, "a", "b")
    assert client.post.call_args.kwargs["json"] == {"name": "a", "description": "b"}
    assert client.put.call_args.kwargs["json"] == {"name": "a", "description": "b"}


@pytest.mark.parametrize(
    ("call", "verb"),
    [
        (lambda api, params: api.post_user_group("a", "b", params=params), "post"),
        (lambda api, params: api.get_user_group(5, params=params), "get"),
        (lambda api, params: api.put_user_group(5, "a", "b", params=params), "put"),
        (lambda api, params: api.post_user_group_user(5, 6, params=params), "post"),
    ],
    ids=["post", "get", "put", "post_user"],
)
def test_forwards_params_untouched(call, verb):
    api, client = offline_api()
    params = {"a": 1}
    call(api, params)
    assert getattr(client, verb).call_args.args[1] == {"a": 1}
    assert params == {"a": 1}


@pytest.mark.parametrize(
    ("call", "resource"),
    [
        (lambda api, params: api.get_user_groups(params=params), "usergroups"),
        (
            lambda api, params: api.get_user_group_users(5, params=params),
            "usergroups/5/users",
        ),
    ],
    ids=["groups", "users"],
)
def test_lists_forward_params_untouched(call, resource):
    api, client = offline_api()
    params = {"a": 1}
    call(api, params)
    assert client.get_all.call_args.args == (resource,)
    assert client.get_all.call_args.kwargs["params"] == {"a": 1}
    assert params == {"a": 1}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_user_group("a", "b"),
        lambda api: api.get_user_group(5),
        lambda api: api.put_user_group(5, "a", "b"),
        lambda api: api.delete_user_group(5),
        lambda api: api.post_user_group_user(5, 6),
        lambda api: api.delete_user_group_user(5, 6),
    ],
    ids=["post", "get", "put", "delete", "post_user", "delete_user"],
)
def test_wraps_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_get_user_groups_without_permission(user_groups_api):
    with pytest.raises(UnauthorizedException):
        user_groups_api.get_user_groups()


# The server checks that a group exists before checking permission: an
# existing group (1) gets 401, a missing one gets 404.
EXISTING_GROUP_ID = 1
MISSING_GROUP_ID = 2147483647


def test_get_user_group_without_permission(user_groups_api):
    with pytest.raises(UnauthorizedException):
        user_groups_api.get_user_group(EXISTING_GROUP_ID)


def test_get_user_group_users_without_permission(user_groups_api):
    with pytest.raises(UnauthorizedException):
        user_groups_api.get_user_group_users(EXISTING_GROUP_ID)


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_user_group(MISSING_GROUP_ID),
        lambda api: api.get_user_group_users(MISSING_GROUP_ID),
    ],
    ids=["group", "users"],
)
def test_missing_user_group_is_not_found(user_groups_api, call):
    with pytest.raises(ResourceNotFoundException):
        call(user_groups_api)


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_user_groups_maps_project():
    api, client = offline_api()
    client.get_all = Mock()
    params = {"project": 1}
    api.get_user_groups(params=params, project=3)
    assert get_all_params(client) == {"project": 3}
    assert params == {"project": 1}
    api.get_user_groups()
    assert get_all_params(client) is None
