from unittest.mock import Mock

import pytest

from py_jama_client.apis.abstract_items_api import AbstractItemsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)


@pytest.fixture(scope="function")
def abstract_items_api(get_test_jama_client):
    api_instance = AbstractItemsAPI(get_test_jama_client)
    return api_instance


def test_get_abstract_items(abstract_items_api, real_project, real_item_type):
    response = abstract_items_api.get_abstract_items(
        project=(real_project,), item_type=(real_item_type,)
    )
    assert response.data != []


def test_get_abstract_item(abstract_items_api, real_abstract_item):
    response = abstract_items_api.get_abstract_item(item_id=real_abstract_item)
    assert response.data != []


def test_get_abstract_item_versions(abstract_items_api, real_abstract_item):
    response = abstract_items_api.get_abstract_item_versions(item_id=real_abstract_item)
    assert response.data != []


def test_get_abstract_item_version(
    abstract_items_api, real_abstract_item, real_abstract_item_version
):
    response = abstract_items_api.get_abstract_item_version(
        item_id=real_abstract_item, version_num=real_abstract_item_version
    )
    assert response.data != []


def test_get_abstract_versioned_item(
    abstract_items_api, real_abstract_item, real_abstract_item_version
):
    response = abstract_items_api.get_abstract_versioned_item(
        item_id=real_abstract_item, version_num=real_abstract_item_version
    )
    assert response.data != []


def test_get_abstract_versioned_relationships(
    abstract_items_api, real_abstract_item, bounded_pages
):
    response = abstract_items_api.get_abstract_versioned_relationships(
        item_id=real_abstract_item,
        timestamp="2026-11-19T00:00:00Z",
        allowed_results_per_page=5,
    )
    assert response.data
    assert len(response.data) == min(bounded_pages["offset_total"], 12)
    for relationship in response.data:
        assert {"id", "fromItem", "toItem", "relationshipType"} <= relationship.keys()
        assert real_abstract_item in {
            relationship["fromItem"][0],
            relationship["toItem"][0],
        }


def test_get_abstract_versioned_relationships_before_item_existed(
    abstract_items_api, real_abstract_item
):
    with pytest.raises(ResourceNotFoundException):
        abstract_items_api.get_abstract_versioned_relationships(
            item_id=real_abstract_item, timestamp="2000-01-01T00:00:00Z"
        )


FILTERS = {
    "project": [1],
    "item_type": [2],
    "document_key": ["K-1"],
    "release": [3],
    "created_date": ["2026-01-01T00:00:00Z"],
    "modified_date": ["2026-01-02T00:00:00Z"],
    "last_activity_date": ["2026-01-03T00:00:00Z"],
    "contains": ["text"],
    "sort_by": ["name.asc"],
}


def test_get_abstract_items_maps_each_filter_to_its_query_parameter():
    client = Mock()
    AbstractItemsAPI(client).get_abstract_items(**FILTERS)
    assert client.get_all.call_args.args[1] == {
        "project": [1],
        "itemType": [2],
        "documentKey": ["K-1"],
        "release": [3],
        "createdDate": ["2026-01-01T00:00:00Z"],
        "modifiedDate": ["2026-01-02T00:00:00Z"],
        "lastActivityDate": ["2026-01-03T00:00:00Z"],
        "contains": ["text"],
        "sortBy": ["name.asc"],
    }


def test_get_abstract_items_sends_no_filters_by_default():
    client = Mock()
    AbstractItemsAPI(client).get_abstract_items()
    assert client.get_all.call_args.args[1] == {}


def test_get_abstract_versioned_relationships_merges_timestamp_into_params():
    client = Mock()
    params = {"a": 1}
    AbstractItemsAPI(client).get_abstract_versioned_relationships(
        5, "2026-01-01T00:00:00Z", params=params
    )
    assert client.get_all.call_args.args[:2] == (
        "abstractitems/5/versionedrelationships",
        {"a": 1, "timestamp": "2026-01-01T00:00:00Z"},
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_abstract_item(item_id=1),
        lambda api: api.get_abstract_item_version(item_id=1, version_num=1),
        lambda api: api.get_abstract_versioned_item(item_id=1, version_num=1),
    ],
    ids=["item", "version", "versioned_item"],
)
def test_abstract_item_reads_wrap_core_exception(call):
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(AbstractItemsAPI(client))


def test_get_abstract_items_maps_include_wildcard():
    client = Mock()
    params = {"includeWildcard": False}
    AbstractItemsAPI(client).get_abstract_items(
        params=params, contains=["word"], include_wildcard=True
    )
    assert client.get_all.call_args.args[1] == {
        "includeWildcard": True,
        "contains": ["word"],
    }
    assert params == {"includeWildcard": False}
    AbstractItemsAPI(client).get_abstract_items(contains=["word"])
    assert "includeWildcard" not in client.get_all.call_args.args[1]


def test_get_abstract_item_version_passes_kwargs_to_the_client():
    client = Mock()
    client.get.return_value.status_code = 200
    AbstractItemsAPI(client).get_abstract_item_version(
        1, 2, timeout=3, headers={"x-custom": "1"}
    )
    kwargs = client.get.call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
