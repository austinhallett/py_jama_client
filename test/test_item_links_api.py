from unittest.mock import Mock

import pytest

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ITEM_ID = 2147483647
MISSING_LINK_ID = 2147483647
LINK_URL = "https://jama.example.com/widget-spec"
LINK_DESCRIPTION = "Widget specification"
OTHER_URL = "https://jama.example.com/widget-spec-v2"
OTHER_DESCRIPTION = "Widget specification, revised"


@pytest.fixture(scope="function")
def items_api(get_test_jama_client):
    return ItemsAPI(get_test_jama_client)


def test_post_item_link(items_api, scratch_item):
    item_id = scratch_item.create()

    response = items_api.post_item_link(item_id, LINK_URL, LINK_DESCRIPTION)

    link_id = response.meta["id"]
    assert isinstance(link_id, int)
    link = items_api.get_item_link(item_id, link_id).data
    assert link["id"] == link_id
    assert link["url"] == LINK_URL
    assert link["description"] == LINK_DESCRIPTION


def test_get_item_links(items_api, scratch_item):
    item_id = scratch_item.create()
    link_id = items_api.post_item_link(item_id, LINK_URL, LINK_DESCRIPTION).meta["id"]

    links = items_api.get_item_links(item_id, allowed_results_per_page=5).data

    assert [link["id"] for link in links] == [link_id]
    assert links[0]["url"] == LINK_URL
    assert links[0]["description"] == LINK_DESCRIPTION


def test_get_item_links_empty(items_api, scratch_item):
    item_id = scratch_item.create()

    assert items_api.get_item_links(item_id, allowed_results_per_page=5).data == []


def test_get_item_link(items_api, scratch_item):
    item_id = scratch_item.create()
    link_id = items_api.post_item_link(item_id, LINK_URL, LINK_DESCRIPTION).meta["id"]

    link = items_api.get_item_link(item_id, link_id).data

    assert link["id"] == link_id
    assert link["url"] == LINK_URL
    assert link["description"] == LINK_DESCRIPTION


def test_put_item_link(items_api, scratch_item):
    item_id = scratch_item.create()
    link_id = items_api.post_item_link(item_id, LINK_URL, LINK_DESCRIPTION).meta["id"]

    assert (
        items_api.put_item_link(item_id, link_id, OTHER_URL, OTHER_DESCRIPTION) == 200
    )

    link = items_api.get_item_link(item_id, link_id).data
    assert link["url"] == OTHER_URL
    assert link["description"] == OTHER_DESCRIPTION


def test_delete_item_link(items_api, scratch_item):
    item_id = scratch_item.create()
    link_id = items_api.post_item_link(item_id, LINK_URL, LINK_DESCRIPTION).meta["id"]

    assert items_api.delete_item_link(item_id, link_id) == 204

    assert items_api.get_item_links(item_id, allowed_results_per_page=5).data == []
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_link(item_id, link_id)


def test_get_item_links_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.get_item_links(MISSING_ITEM_ID, allowed_results_per_page=5)
    assert excinfo.value.status_code == 404


def test_post_item_link_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.post_item_link(MISSING_ITEM_ID, LINK_URL, LINK_DESCRIPTION)
    assert excinfo.value.status_code == 404


def test_get_item_link_unknown_link(items_api, scratch_item):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.get_item_link(item_id, MISSING_LINK_ID)
    assert excinfo.value.status_code == 404


def test_put_item_link_unknown_link(items_api, scratch_item):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.put_item_link(item_id, MISSING_LINK_ID, OTHER_URL, OTHER_DESCRIPTION)
    assert excinfo.value.status_code == 404


def test_delete_item_link_unknown_link(items_api, scratch_item):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_link(item_id, MISSING_LINK_ID)
    assert excinfo.value.status_code == 404


def test_delete_item_link_twice(items_api, scratch_item):
    item_id = scratch_item.create()
    link_id = items_api.post_item_link(item_id, LINK_URL, LINK_DESCRIPTION).meta["id"]
    assert items_api.delete_item_link(item_id, link_id) == 204

    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_link(item_id, link_id)
    assert excinfo.value.status_code == 404


def offline_api():
    client = Mock()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=200,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text="",
        )
    client.delete.return_value.status_code = 204
    return ItemsAPI(client), client


def test_link_methods_build_requests_without_mutating_params():
    api, client = offline_api()
    params = {"a": 1}
    api.get_item_link(5, 6, params=params, timeout=3)
    client.get.assert_called_with("items/5/links/6", params, timeout=3)
    api.post_item_link(5, LINK_URL, LINK_DESCRIPTION, params=params)
    client.post.assert_called_with(
        "items/5/links",
        params,
        json={"url": LINK_URL, "description": LINK_DESCRIPTION},
    )
    assert api.put_item_link(5, 6, OTHER_URL, OTHER_DESCRIPTION, params=params) == 200
    client.put.assert_called_with(
        "items/5/links/6",
        params,
        json={"url": OTHER_URL, "description": OTHER_DESCRIPTION},
    )
    assert api.delete_item_link(5, 6, params=params, timeout=3) == 204
    client.delete.assert_called_with("items/5/links/6", params=params, timeout=3)
    api.get_item_links(5, params=params, allowed_results_per_page=5)
    client.get_all.assert_called_with(
        "items/5/links", params, allowed_results_per_page=5
    )
    assert params == {"a": 1}


def test_link_methods_wrap_core_exceptions():
    api, client = offline_api()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    calls = [
        lambda: api.get_item_link(5, 6),
        lambda: api.post_item_link(5, LINK_URL, LINK_DESCRIPTION),
        lambda: api.put_item_link(5, 6, OTHER_URL, OTHER_DESCRIPTION),
        lambda: api.delete_item_link(5, 6),
    ]
    for call in calls:
        with pytest.raises(APIException):
            call()
