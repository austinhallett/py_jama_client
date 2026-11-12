from unittest.mock import Mock

import pytest

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.apis.tags_api import TagsAPI
from py_jama_client.exceptions import ResourceNotFoundException


@pytest.fixture(scope="function")
def items_api(get_test_jama_client, bounded_live_pages):
    return ItemsAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def relationship_items(items_api, real_relationship):
    relationship = RelationshipsAPI(items_api.client).get_relationship(
        relationship_id=real_relationship
    ).data
    return relationship["fromItem"], relationship["toItem"]


@pytest.fixture(scope="function")
def populated_tagged_item(items_api, real_project):
    tags = TagsAPI(items_api.client).get_tags(project_id=real_project).data
    for tag in tags:
        tagged_items = items_api.get_tagged_items(tag_id=tag["id"]).data
        if tagged_items:
            return tag["id"], tagged_items[0]["id"]
    pytest.skip("No populated tag is available in the sample project.")


@pytest.fixture(scope="function")
def item_synced_items(items_api, relationship_items):
    for item_id in relationship_items:
        synced_items = items_api.get_items_synceditems(item_id=item_id).data
        if synced_items:
            return item_id, synced_items
    pytest.skip("No synchronized item is available for the sample relationship.")


def test_get_items(items_api, real_project, bounded_live_pages):
    response = items_api.get_items(project_id=real_project)
    total_results = bounded_live_pages["offset_total"]
    if isinstance(total_results, int) and total_results < 12:
        pytest.skip("The sample project has fewer than 12 items.")
    assert len(response.data) == 12
    assert bounded_live_pages["offset"] == [5, 5, 2]


def test_get_item(items_api, real_abstract_item):
    response = items_api.get_item(item_id=real_abstract_item)
    assert response.data is not None


def test_get_tagged_items(items_api, populated_tagged_item):
    tag_id, item_id = populated_tagged_item
    response = items_api.get_tagged_items(tag_id=tag_id)
    assert item_id in {item["id"] for item in response.data}


def test_get_items_upstream_relationships(items_api, relationship_items):
    _, target_item = relationship_items
    response = items_api.get_items_upstream_relationships(
        item_id=target_item
    )
    assert response.data


def test_get_items_downstream_related(items_api, relationship_items):
    source_item, _ = relationship_items
    response = items_api.get_items_downstream_related(
        item_id=source_item
    )
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
    response = items_api.get_items_upstream_related(
        item_id=target_item
    )
    assert response.data


def test_get_item_workflow_transitions(items_api, real_abstract_item):
    try:
        response = items_api.get_item_workflow_transitions(
            item_id=real_abstract_item
        )
    except ResourceNotFoundException as error:
        if error.reason and error.reason.startswith(
            "Workflow is not associated with the item"
        ):
            pytest.skip("No workflow is associated with this fixture item.")
        raise
    if not response.data:
        pytest.skip("No workflow transition is available for this fixture item.")
    assert response.data


def test_get_item_children(items_api, real_abstract_item):
    response = items_api.get_item_children(item_id=real_abstract_item)
    if not response.data:
        pytest.skip("The fixture item has no child items.")
    assert response.data


def test_get_items_synceditems(item_synced_items):
    _, synced_items = item_synced_items
    assert synced_items


def test_get_items_synceditems_status(items_api, item_synced_items):
    item_id, synced_items = item_synced_items
    response = items_api.get_items_synceditems_status(
        item_id=item_id,
        synced_item_id=synced_items[0]["id"],
    )
    assert response.data is not None


def test_get_item_version(items_api, real_abstract_item, real_abstract_item_version):
    response = items_api.get_item_version(
        item_id=real_abstract_item,
        version_num=real_abstract_item_version,
    )
    assert response.data is not None


def test_get_versioned_item(
    items_api, real_abstract_item, real_abstract_item_version
):
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