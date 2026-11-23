from unittest.mock import Mock

import pytest

from py_jama_client.apis.item_types_api import ItemTypesAPI
from py_jama_client.apis.pick_lists_api import PickListsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_PICK_LIST_ID = 2147483647


@pytest.fixture(scope="function")
def pick_lists_api(get_test_jama_client, bounded_pages):
    return PickListsAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def status_pick_list(get_test_jama_client, real_item_type):
    fields = (
        ItemTypesAPI(get_test_jama_client).get_item_type(real_item_type).data["fields"]
    )
    for field in fields:
        if field["name"] == "status" and field.get("pickList"):
            return field["pickList"]
    pytest.fail("The fixture item type has no status pick list.")


def test_get_pick_lists(pick_lists_api, bounded_pages):
    response = pick_lists_api.get_pick_lists()
    assert len(response.data) == min(bounded_pages["offset_total"], 12)
    assert all({"id", "name", "type"} <= set(p) for p in response.data)
    assert {p["type"] for p in response.data} == {"picklists"}


def test_get_pick_list(pick_lists_api, status_pick_list):
    response = pick_lists_api.get_pick_list(status_pick_list)
    assert response.data["id"] == status_pick_list
    assert response.data["type"] == "picklists"
    assert isinstance(response.data["name"], str)


def test_get_pick_list_missing_pick_list(pick_lists_api):
    with pytest.raises(ResourceNotFoundException):
        pick_lists_api.get_pick_list(MISSING_PICK_LIST_ID)


def test_get_pick_list_options(pick_lists_api, status_pick_list):
    response = pick_lists_api.get_pick_list_options(status_pick_list)
    assert response.data
    assert {o["pickList"] for o in response.data} == {status_pick_list}
    assert all({"id", "name", "sortOrder"} <= set(o) for o in response.data)


def test_get_pick_list_options_missing_pick_list(pick_lists_api):
    with pytest.raises(ResourceNotFoundException):
        pick_lists_api.get_pick_list_options(MISSING_PICK_LIST_ID)


def test_post_pick_list_docs(pick_lists_api):
    # The docs give no example request body, only the RequestPickList model.
    response = pick_lists_api.post_pick_list(
        "Example pick list", "Example description", 0
    )
    assert response.meta["id"] == 101
    assert response.meta["location"].endswith("/picklists/101")


def test_delete_pick_list_docs(pick_lists_api):
    assert pick_lists_api.delete_pick_list(5) == 204


def test_post_pick_list_option_docs(pick_lists_api):
    # The docs give no example request body, only the RequestPickListOption model.
    response = pick_lists_api.post_pick_list_option(
        5,
        {
            "name": "Example option",
            "description": "Example description",
            "value": "example",
            "color": "#336699",
            "sortOrder": 1,
            "infotip": "Example infotip",
            "default": False,
        },
    )
    assert response.meta["id"] == 102
    assert response.meta["location"].endswith("/picklistoptions/102")


def offline_api():
    client = Mock()
    for verb in ("post", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=201, json=Mock(return_value={"meta": {}}), text=""
        )
    return PickListsAPI(client), client


def test_get_pick_list_wraps_core_exception():
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        PickListsAPI(client).get_pick_list(1)


@pytest.mark.parametrize(
    "call",
    [
        lambda api, params: api.post_pick_list("a", "b", 0, params=params),
        lambda api, params: api.post_pick_list_option(5, {}, params=params),
    ],
    ids=["pick_list", "option"],
)
def test_admin_posts_forward_params_untouched(call):
    api, client = offline_api()
    params = {"a": 1}
    call(api, params)
    assert client.post.call_args.args[1] == {"a": 1}
    assert params == {"a": 1}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_pick_list("a", "b", 0),
        lambda api: api.post_pick_list_option(5, {}),
        lambda api: api.delete_pick_list(5),
    ],
    ids=["pick_list", "option", "delete"],
)
def test_admin_writes_wrap_core_exception(call):
    api, client = offline_api()
    for verb in ("post", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


@pytest.mark.parametrize(
    ("method", "args", "verb"),
    [
        ("get_pick_lists", (), "get_all"),
        ("get_pick_list", (1,), "get"),
        ("get_pick_list_options", (1,), "get_all"),
    ],
)
def test_pick_list_reads_pass_kwargs_to_the_client(method, args, verb):
    client = Mock()
    getattr(client, verb).return_value.status_code = 200
    getattr(PickListsAPI(client), method)(*args, timeout=3, headers={"x-custom": "1"})
    kwargs = getattr(client, verb).call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
