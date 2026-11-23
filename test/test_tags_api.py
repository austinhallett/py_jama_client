from unittest.mock import Mock

import pytest

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.apis.tags_api import TagsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_TAG_ID = 2147483647


@pytest.fixture(scope="function")
def tags_api(get_test_jama_client):
    api_instance = TagsAPI(get_test_jama_client)
    return api_instance


def test_get_tags(tags_api, real_project):
    response = tags_api.get_tags(project_id=real_project)
    assert response.data != []


def test_get_tag(tags_api, real_tag):
    response = tags_api.get_tag(tag_id=real_tag)
    assert response.data is not None


@pytest.fixture(scope="function")
def populated_tag_item(tags_api, real_project):
    for tag in tags_api.get_tags(project_id=real_project).data:
        items = tags_api.get_tag_items(tag_id=tag["id"]).data
        if items:
            return tag["id"], items[0]["id"]
    pytest.fail("No populated tag is available in the sample project.")


def test_get_tag_items(tags_api, populated_tag_item):
    tag_id, item_id = populated_tag_item
    response = tags_api.get_tag_items(tag_id=tag_id)
    assert item_id in {item["id"] for item in response.data}


@pytest.fixture(scope="function")
def scratch_tag(request, tags_api, real_project):
    """Factory for throwaway tags, deleted on teardown even if the test failed
    or already deleted them."""
    created = []

    def create(suffix=""):
        name = f"zz-char-{request.node.name}" + (f"-{suffix}" if suffix else "")
        tag_id = tags_api.post_tag(name, real_project).meta["id"]
        created.append(tag_id)
        return tag_id, name

    yield create
    failures = []
    for tag_id in reversed(created):
        try:
            tags_api.delete_tag(tag_id)
        except ResourceNotFoundException:
            pass
        except Exception as error:  # noqa: BLE001
            failures.append((tag_id, str(error)))
    assert not failures, f"scratch tags left behind: {failures}"


def test_get_tags_merges_project_into_caller_params(tags_api, real_project, real_tag):
    # maxResults is overridden by allowed_results_per_page; it only shows that
    # the caller's dict is left alone.
    params = {"maxResults": 5}
    response = tags_api.get_tags(real_project, params=params)
    assert {tag["project"] for tag in response.data} == {real_project}
    assert real_tag in {tag["id"] for tag in response.data}
    assert params == {"maxResults": 5}


def test_post_tag(tags_api, scratch_tag, real_project):
    tag_id, name = scratch_tag()
    tag = tags_api.get_tag(tag_id).data
    assert tag["id"] == tag_id
    assert tag["name"] == name
    assert tag["project"] == real_project


def test_put_tag(tags_api, scratch_tag, real_project):
    tag_id, name = scratch_tag()
    tags_api.put_tag(tag_id, f"{name}-renamed", real_project)
    tag = tags_api.get_tag(tag_id).data
    assert tag["name"] == f"{name}-renamed"
    assert tag["project"] == real_project


def test_delete_tag(tags_api, scratch_tag):
    tag_id, _ = scratch_tag()
    assert tags_api.delete_tag(tag_id) == 204
    with pytest.raises(ResourceNotFoundException):
        tags_api.get_tag(tag_id)


def test_delete_tag_unknown_tag(tags_api):
    with pytest.raises(ResourceNotFoundException):
        tags_api.delete_tag(MISSING_TAG_ID)


def test_get_tag_items_of_scratch_tag(
    tags_api, scratch_tag, scratch_item, get_test_jama_client
):
    tag_id, _ = scratch_tag()
    item_id = scratch_item.create()
    ItemsAPI(get_test_jama_client).post_item_tag(item_id, tag_id)
    items = tags_api.get_tag_items(tag_id, allowed_results_per_page=5).data
    assert [item["id"] for item in items] == [item_id]


def offline_api():
    client = Mock()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
        )
    return TagsAPI(client), client


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_tag("n", 7),
        lambda api: api.get_tag(5),
        lambda api: api.put_tag(5, "n", 7),
        lambda api: api.delete_tag(5),
    ],
    ids=["post", "get", "put", "delete"],
)
def test_tags_wrap_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_get_tag_passes_kwargs_to_the_client():
    client = Mock()
    client.get.return_value.status_code = 200
    TagsAPI(client).get_tag(1, timeout=3, headers={"x-custom": "1"})
    kwargs = client.get.call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
