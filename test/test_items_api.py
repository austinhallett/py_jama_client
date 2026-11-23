from unittest.mock import Mock

import pytest

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.apis.tags_api import TagsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ITEM_ID = 2147483647


@pytest.fixture(scope="function")
def items_api(get_test_jama_client, bounded_pages):
    return ItemsAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def relationship_items(items_api, real_relationship):
    relationship = (
        RelationshipsAPI(items_api.client)
        .get_relationship(relationship_id=real_relationship)
        .data
    )
    return relationship["fromItem"], relationship["toItem"]


@pytest.fixture(scope="function")
def populated_tagged_item(items_api, real_project):
    tags = TagsAPI(items_api.client).get_tags(project_id=real_project).data
    for tag in tags:
        tagged_items = items_api.get_tagged_items(tag_id=tag["id"]).data
        if tagged_items:
            return tag["id"], tagged_items[0]["id"]
    pytest.fail("No populated tag is available in the sample project.")


@pytest.fixture(scope="function")
def item_synced_items(items_api, relationship_items):
    for item_id in relationship_items:
        synced_items = items_api.get_items_synceditems(item_id=item_id).data
        if synced_items:
            return item_id, synced_items
    pytest.fail("No synchronized item is available for the sample relationship.")


def test_get_items(items_api, real_project, bounded_pages):
    response = items_api.get_items(project_id=real_project)
    assert bounded_pages["offset_total"] >= 12
    assert len(response.data) == 12
    assert bounded_pages["offset"] == [5, 5, 2]


def test_get_item(items_api, real_abstract_item):
    response = items_api.get_item(item_id=real_abstract_item)
    assert response.data is not None


def test_get_tagged_items(items_api, populated_tagged_item):
    tag_id, item_id = populated_tagged_item
    response = items_api.get_tagged_items(tag_id=tag_id)
    assert item_id in {item["id"] for item in response.data}


def test_get_items_upstream_relationships(items_api, relationship_items):
    _, target_item = relationship_items
    response = items_api.get_items_upstream_relationships(item_id=target_item)
    assert response.data


def test_get_items_downstream_related(items_api, relationship_items):
    source_item, _ = relationship_items
    response = items_api.get_items_downstream_related(item_id=source_item)
    assert response.data


def test_get_items_downstream_relationships(
    items_api, relationship_items, real_project, monkeypatch
):
    source_item, _ = relationship_items
    params = {"project": real_project}
    headers = {"Accept": "application/json"}
    get_all = Mock(wraps=items_api.client.get_all)
    monkeypatch.setattr(items_api.client, "get_all", get_all)

    response = items_api.get_items_downstream_relationships(
        item_id=source_item,
        params=params,
        allowed_results_per_page=7,
        headers=headers,
    )

    assert response.data
    get_all.assert_called_once_with(
        f"items/{source_item}/downstreamrelationships",
        params=params,
        allowed_results_per_page=7,
        headers=headers,
    )


def test_get_items_upstream_related(items_api, relationship_items):
    _, target_item = relationship_items
    response = items_api.get_items_upstream_related(item_id=target_item)
    assert response.data


def test_get_item_workflow_transitions_without_workflow(items_api, real_abstract_item):
    with pytest.raises(ResourceNotFoundException) as error:
        items_api.get_item_workflow_transitions(item_id=real_abstract_item)
    assert error.value.reason
    assert error.value.reason.startswith("Workflow is not associated with the item")


def test_get_item_children(items_api, real_abstract_item):
    response = items_api.get_item_children(item_id=real_abstract_item)
    assert response.data
    for child in response.data:
        assert child["location"]["parent"]["item"] == real_abstract_item


def test_get_items_synceditems(item_synced_items):
    item_id, synced_items = item_synced_items
    for item in synced_items:
        assert isinstance(item["id"], int)
        assert item["id"] != item_id


def test_get_items_synceditems_status(items_api, item_synced_items):
    item_id, synced_items = item_synced_items
    response = items_api.get_items_synceditems_status(
        item_id=item_id,
        synced_item_id=synced_items[0]["id"],
    )
    assert isinstance(response.data["inSync"], bool)


def test_get_item_version(items_api, real_abstract_item, real_abstract_item_version):
    response = items_api.get_item_version(
        item_id=real_abstract_item,
        version_num=real_abstract_item_version,
    )
    assert response.data is not None


def test_get_versioned_item(items_api, real_abstract_item, real_abstract_item_version):
    response = items_api.get_versioned_item(
        item_id=real_abstract_item,
        version_num=real_abstract_item_version,
    )
    assert response.data is not None


def test_get_item_versions(items_api, real_abstract_item):
    response = items_api.get_item_versions(item_id=real_abstract_item)
    assert response.data != []


def test_get_item_lock(items_api, real_abstract_item):
    response = items_api.get_item_lock(item_id=real_abstract_item)
    assert response.data is not None


def test_get_item_tags(items_api, populated_tagged_item):
    _, item_id = populated_tagged_item
    response = items_api.get_item_tags(item_id=item_id)
    assert response.data


def test_get_item_tag(items_api, populated_tagged_item):
    tag_id, item_id = populated_tagged_item
    response = items_api.get_item_tag(item_id=item_id, tag_id=tag_id)
    assert response.data["id"] == tag_id
    assert "name" in response.data


def test_get_item_tag_not_on_item(items_api, populated_tagged_item, real_project):
    _, item_id = populated_tagged_item
    on_item = {tag["id"] for tag in items_api.get_item_tags(item_id=item_id).data}
    tags = TagsAPI(items_api.client).get_tags(project_id=real_project).data
    other_tags = [tag["id"] for tag in tags if tag["id"] not in on_item]
    assert other_tags
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_tag(item_id=item_id, tag_id=other_tags[0])


def test_get_item_tag_unknown_tag(items_api, populated_tagged_item):
    _, item_id = populated_tagged_item
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_tag(item_id=item_id, tag_id=MISSING_ITEM_ID)


def test_get_item_tag_missing_item(items_api, real_tag):
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_tag(item_id=MISSING_ITEM_ID, tag_id=real_tag)


def test_get_item_attachments(items_api, real_attached_item):
    response = items_api.get_item_attachments(
        item_id=real_attached_item, allowed_results_per_page=5
    )
    assert response.data
    assert all("id" in attachment for attachment in response.data)


def test_get_item_attachments_missing_item(items_api):
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_attachments(
            item_id=MISSING_ITEM_ID, allowed_results_per_page=5
        )


def test_get_item_location(items_api, real_abstract_item):
    response = items_api.get_item_location(item_id=real_abstract_item)
    assert "parent" in response.data
    assert "sortOrder" in response.data


def test_get_item_location_missing_item(items_api):
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_location(item_id=MISSING_ITEM_ID)


def test_get_item_parent(items_api, real_abstract_item):
    response = items_api.get_item_parent(item_id=real_abstract_item)
    assert "id" in response.data
    assert "type" in response.data


def test_get_item_parent_missing_item(items_api):
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_parent(item_id=MISSING_ITEM_ID)


def test_get_item_activities(items_api, real_abstract_item):
    response = items_api.get_item_activities(
        item_id=real_abstract_item, allowed_results_per_page=5
    )
    assert response.data
    assert all({"id", "eventType", "objectType"} <= set(a) for a in response.data)
    # Review activities (objectType REVISION_ITEM) have no "item" key.
    assert {a["item"] for a in response.data if "item" in a} == {real_abstract_item}
    assert all("item" in a for a in response.data if a["objectType"] != "REVISION_ITEM")


def test_get_item_activities_missing_item(items_api):
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_activities(
            item_id=MISSING_ITEM_ID, allowed_results_per_page=5
        )


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_item_tag(item_id=1, tag_id=2),
        lambda api: api.get_item_location(item_id=1),
        lambda api: api.get_item_parent(item_id=1),
        lambda api: api.get_item(item_id=1),
        lambda api: api.get_items_synceditems_status(item_id=1, synced_item_id=2),
        lambda api: api.get_item_version(item_id=1, version_num=1),
        lambda api: api.get_versioned_item(item_id=1, version_num=1),
        lambda api: api.get_item_lock(item_id=1),
    ],
    ids=[
        "tag",
        "location",
        "parent",
        "item",
        "synceditems_status",
        "version",
        "versioned_item",
        "lock",
    ],
)
def test_item_reads_wrap_core_exception(call):
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(ItemsAPI(client))


def test_get_items_merges_project_into_caller_params():
    client = Mock()
    ItemsAPI(client).get_items(7, params={"a": 1})
    assert client.get_all.call_args.kwargs["params"] == {"a": 1, "project": 7}


def test_get_item_workflow_transitions_synthetic(get_test_jama_client):
    response = ItemsAPI(get_test_jama_client).get_item_workflow_transitions(item_id=1)
    assert [transition["id"] for transition in response.data] == ["101", "102"]
    for transition in response.data:
        assert {"id", "action", "newStatus"} <= transition.keys()


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_items_maps_root_only():
    client = Mock()
    params = {"rootOnly": False}
    ItemsAPI(client).get_items(7, params=params, root_only=True)
    assert get_all_params(client) == {"rootOnly": True, "project": 7}
    assert params == {"rootOnly": False}
    ItemsAPI(client).get_items(7)
    assert get_all_params(client) == {"project": 7}


def test_get_item_comments_maps_root_comments_only():
    client = Mock()
    params = {"rootCommentsOnly": False}
    ItemsAPI(client).get_item_comments(5, params=params, root_comments_only=True)
    assert get_all_params(client) == {"rootCommentsOnly": True}
    assert params == {"rootCommentsOnly": False}
    ItemsAPI(client).get_item_comments(5)
    assert get_all_params(client) is None


@pytest.mark.parametrize(
    ("method", "args", "verb"),
    [
        ("get_items", (1,), "get_all"),
        ("get_items_synceditems_status", (1, 2), "get"),
        ("get_item_version", (1, 2), "get"),
        ("get_versioned_item", (1, 2), "get"),
        ("get_item_versions", (1,), "get_all"),
        ("get_item_tags", (1,), "get_all"),
    ],
)
def test_item_reads_pass_kwargs_to_the_client(method, args, verb):
    client = Mock()
    getattr(client, verb).return_value.status_code = 200
    getattr(ItemsAPI(client), method)(*args, timeout=3, headers={"x-custom": "1"})
    kwargs = getattr(client, verb).call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
