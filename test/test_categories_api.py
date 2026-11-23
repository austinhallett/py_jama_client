from unittest.mock import Mock

import pytest

from py_jama_client.apis.categories_api import CategoriesAPI
from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ITEM_ID = 2147483647
MISSING_CATEGORY_PATH_ID = 2147483647
MISSING_BASELINE_ID = 2147483647
# MOCK's existing "Bootloader" category path
CATEGORY_PATH_ID = 4


@pytest.fixture(scope="function")
def categories_api(get_test_jama_client):
    return CategoriesAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def items_api(get_test_jama_client):
    return ItemsAPI(get_test_jama_client)


def applied_ids(items_api, item_id):
    return [
        category["categoryPathId"]
        for category in items_api.get_item_categories(
            item_id, allowed_results_per_page=5
        ).data
    ]


def test_get_categories(categories_api, real_project):
    categories = categories_api.get_categories(
        params={"projectId": real_project}, allowed_results_per_page=5
    ).data

    assert categories
    for category in categories:
        assert {"categoryId", "categoryName", "categoryPathId"} <= category.keys()
    assert CATEGORY_PATH_ID in {c["categoryPathId"] for c in categories}


def test_get_categories_by_name_without_match(categories_api):
    response = categories_api.get_categories(
        params={"categoryName": "zz-char-no-such-category"},
        allowed_results_per_page=5,
    )
    assert response.data == []


def test_post_item_categories(items_api, scratch_item):
    item_id = scratch_item.create()
    assert applied_ids(items_api, item_id) == []

    assert items_api.post_item_categories(item_id, [CATEGORY_PATH_ID]) == 200

    categories = items_api.get_item_categories(item_id, allowed_results_per_page=5).data
    assert [c["categoryPathId"] for c in categories] == [CATEGORY_PATH_ID]
    assert {"categoryPathName", "itemVersionIdApplied", "pathIdsToRoot"} <= (
        categories[0].keys()
    )


def test_get_item_categories_empty(items_api, scratch_item):
    item_id = scratch_item.create()
    assert items_api.get_item_categories(item_id, allowed_results_per_page=5).data == []


def test_delete_item_categories(items_api, scratch_item):
    item_id = scratch_item.create()
    assert items_api.post_item_categories(item_id, [CATEGORY_PATH_ID]) == 200
    assert applied_ids(items_api, item_id) == [CATEGORY_PATH_ID]

    assert items_api.delete_item_categories(item_id, [CATEGORY_PATH_ID]) == 200

    assert applied_ids(items_api, item_id) == []


def test_get_item_categories_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.get_item_categories(MISSING_ITEM_ID, allowed_results_per_page=5)
    assert excinfo.value.status_code == 404


def test_post_item_categories_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.post_item_categories(MISSING_ITEM_ID, [CATEGORY_PATH_ID])
    assert excinfo.value.status_code == 404


def test_delete_item_categories_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_categories(MISSING_ITEM_ID, [CATEGORY_PATH_ID])
    assert excinfo.value.status_code == 404


def test_post_item_categories_unknown_category(items_api, scratch_item):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.post_item_categories(item_id, [MISSING_CATEGORY_PATH_ID])
    assert excinfo.value.status_code == 404
    assert applied_ids(items_api, item_id) == []


def test_delete_item_categories_not_applied(items_api, scratch_item):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_categories(item_id, [CATEGORY_PATH_ID])
    assert excinfo.value.status_code == 404
    assert applied_ids(items_api, item_id) == []


def test_get_item_versioned_categories(items_api, scratch_item):
    item_id = scratch_item.create()
    assert items_api.post_item_categories(item_id, [CATEGORY_PATH_ID]) == 200
    applied = items_api.get_item_categories(item_id, allowed_results_per_page=5).data

    response = items_api.get_item_versioned_categories(
        item_id, 1, allowed_results_per_page=5
    )

    assert [c["categoryPathName"] for c in response.data] == [
        c["categoryPathName"] for c in applied
    ]
    assert [c["itemVersionIdApplied"] for c in response.data] == [1]


def test_get_item_versioned_categories_before_apply(items_api, scratch_item):
    item_id = scratch_item.create()
    assert items_api.get_item_versioned_categories(item_id, 1).data == []


def test_get_item_versioned_categories_unknown_version(items_api, scratch_item):
    item_id = scratch_item.create()
    assert items_api.get_item_versioned_categories(item_id, 99).data == []


def test_get_item_versioned_categories_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.get_item_versioned_categories(MISSING_ITEM_ID, 1)
    assert excinfo.value.status_code == 404


def test_get_item_baselined_categories_item_in_baseline(
    items_api, real_baseline_versioned_item, real_baseline
):
    response = items_api.get_item_baselined_categories(
        real_baseline_versioned_item, real_baseline, allowed_results_per_page=5
    )
    assert response.data == []


def test_get_item_baselined_categories_item_outside_baseline(
    items_api, scratch_item, real_baseline
):
    item_id = scratch_item.create()
    assert items_api.post_item_categories(item_id, [CATEGORY_PATH_ID]) == 200
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.get_item_baselined_categories(item_id, real_baseline)
    assert excinfo.value.status_code == 404


def test_get_item_baselined_categories_unknown_baseline(
    items_api, real_baseline_versioned_item
):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.get_item_baselined_categories(
            real_baseline_versioned_item, MISSING_BASELINE_ID
        )
    assert excinfo.value.status_code == 404


def test_post_category_synthetic(categories_api):
    response = categories_api.post_category("Widgets/Gadgets")
    assert response.data == 9001


def test_put_category_visibility_synthetic(categories_api):
    assert categories_api.put_category_visibility(9001, [5], False) == 200


MISSING_ID = 2147483647


def test_delete_category_docs(categories_api):
    assert categories_api.delete_category(1) == 204


def test_delete_category_path_docs(categories_api):
    assert categories_api.delete_category_path(2) == 204


def test_copy_category_path_docs(categories_api):
    response = categories_api.copy_category_path(2, 3)
    assert response.meta["status"] == "Created"
    assert response.meta["id"] == 4


def test_move_category_path_docs(categories_api):
    assert categories_api.move_category_path(2, 3) == 200


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.delete_category(MISSING_ID),
        lambda api: api.delete_category_path(MISSING_ID),
        lambda api: api.copy_category_path(MISSING_ID, MISSING_ID),
        lambda api: api.move_category_path(MISSING_ID, MISSING_ID),
    ],
    ids=["delete_category", "delete_category_path", "copy", "move"],
)
def test_category_operations_on_missing_ids(categories_api, call):
    with pytest.raises(ResourceNotFoundException):
        call(categories_api)


def offline_client(status_code=200):
    client = Mock()
    for verb in ("get", "post", "put", "delete", "delete_with_body"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text="",
        )
    return client


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_category("a"),
        lambda api: api.put_category_visibility(1, [], True),
        lambda api: api.delete_category(1),
        lambda api: api.delete_category_path(1),
        lambda api: api.copy_category_path(1, 2),
        lambda api: api.move_category_path(1, 2),
    ],
)
def test_category_writes_wrap_core_exceptions(call):
    client = offline_client()
    client.post.side_effect = CoreException("boom")
    client.put.side_effect = CoreException("boom")
    client.delete.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(CategoriesAPI(client))


def test_category_writes_send_json_bodies_without_mutating_params():
    client = offline_client()
    api = CategoriesAPI(client)
    params = {"a": 1}
    api.post_category("a/b", params=params, timeout=3)
    client.post.assert_called_with(
        "categories", params, json={"path": "a/b"}, timeout=3
    )
    assert api.put_category_visibility(7, [1, 2], False, params=params) == 200
    client.put.assert_called_with(
        "categories/7/visibility",
        params,
        json={"projectIds": [1, 2], "isGlobal": False},
    )
    assert params == {"a": 1}


def test_category_path_operations_build_requests():
    client = offline_client()
    api = CategoriesAPI(client)
    params = {"a": 1}
    api.copy_category_path(2, 3, params=params, timeout=3)
    client.post.assert_called_with(
        "categorypaths/2/copy",
        params,
        json={"destinationParentCategoryPathId": 3},
        timeout=3,
    )
    api.move_category_path(2, 3, params=params)
    client.put.assert_called_with(
        "categorypaths/2/move",
        params={"a": 1, "destinationParentCategoryPathId": 3},
    )
    api.delete_category(5, params=params)
    client.delete.assert_called_with("categories/5", params=params)
    api.delete_category_path(6)
    client.delete.assert_called_with("categorypaths/6", params=None)
    assert params == {"a": 1}


def test_get_categories_maps_filters():
    client = offline_client()
    params = {"a": 1}
    CategoriesAPI(client).get_categories(
        params=params, category_name="Hardware", project_id=375
    )
    client.get_all.assert_called_with(
        "categories",
        {"a": 1, "categoryName": "Hardware", "projectId": 375},
        allowed_results_per_page=50,
    )
    assert params == {"a": 1}


def test_get_categories_passes_params_to_get_all():
    client = offline_client()
    params = {"categoryName": "x"}
    CategoriesAPI(client).get_categories(params=params, allowed_results_per_page=5)
    client.get_all.assert_called_with("categories", params, allowed_results_per_page=5)


def test_item_category_methods_build_requests():
    client = offline_client()
    api = ItemsAPI(client)
    params = {"a": 1}
    assert api.post_item_categories(5, [4], params=params) == 200
    client.post.assert_called_with(
        "items/5/categories", params, json={"categoryPathIds": [4]}
    )
    assert api.delete_item_categories(5, [4], params=params, timeout=3) == 200
    client.delete_with_body.assert_called_with(
        "items/5/categories", {"categoryPathIds": [4]}, params=params, timeout=3
    )
    api.get_item_baselined_categories(5, 9, params=params)
    client.get_all.assert_called_with(
        "items/5/baselinedcategories",
        {"a": 1, "baselineId": 9},
        allowed_results_per_page=50,
    )
    api.get_item_versioned_categories(5, 2, params=params)
    client.get_all.assert_called_with(
        "items/5/versionedcategories",
        {"a": 1, "versionNumber": 2},
        allowed_results_per_page=50,
    )
    api.get_item_versioned_categories(5, 2)
    client.get_all.assert_called_with(
        "items/5/versionedcategories",
        {"versionNumber": 2},
        allowed_results_per_page=50,
    )
    assert params == {"a": 1}


def test_item_category_writes_wrap_core_exceptions():
    client = offline_client()
    client.post.side_effect = CoreException("boom")
    client.delete_with_body.side_effect = CoreException("boom")
    api = ItemsAPI(client)
    with pytest.raises(APIException):
        api.post_item_categories(5, [4])
    with pytest.raises(APIException):
        api.delete_item_categories(5, [4])
