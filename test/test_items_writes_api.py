import time
import warnings
from unittest.mock import Mock

import pytest

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.exceptions import (
    APIClientException,
    APIException,
    APIServerException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ITEM_ID = 2147483647


@pytest.fixture(scope="function")
def items_api(get_test_jama_client):
    return ItemsAPI(get_test_jama_client)


def wait_for(check, attempts=10):
    for _ in range(attempts):
        if check():
            return True
        time.sleep(0.5)
    return False


def test_delete_item_tag(items_api, scratch_item, real_tag):
    item_id = scratch_item.create()
    assert items_api.post_item_tag(item_id, real_tag) == 201
    assert real_tag in {tag["id"] for tag in items_api.get_item_tags(item_id).data}

    assert items_api.delete_item_tag(item_id, real_tag) == 204

    assert real_tag not in {tag["id"] for tag in items_api.get_item_tags(item_id).data}
    with pytest.raises(ResourceNotFoundException):
        items_api.get_item_tag(item_id, real_tag)


def test_delete_item_tag_real_tag_not_on_item(items_api, scratch_item, real_tag):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_tag(item_id, real_tag)
    assert excinfo.value.status_code == 404


def test_delete_item_tag_unknown_item(items_api, real_tag):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_tag(MISSING_ITEM_ID, real_tag)
    assert excinfo.value.status_code == 404


def test_delete_item_synceditem(items_api, scratch_item):
    pool_item = scratch_item.create("pool")
    source_item = scratch_item.create("source")
    items_api.post_item_sync(source_item, pool_item, params=None)
    synced = items_api.get_items_synceditems(pool_item).data
    assert [item["id"] for item in synced] == [source_item]

    assert items_api.delete_item_synceditem(pool_item, source_item) == 204

    assert items_api.get_items_synceditems(pool_item).data == []
    assert items_api.get_items_synceditems(source_item).data == []


def test_delete_item_synceditem_items_not_synced(items_api, scratch_item):
    first = scratch_item.create("first")
    second = scratch_item.create("second")
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_synceditem(first, second)
    assert excinfo.value.status_code == 404
    assert excinfo.value.reason
    assert "does not share a Global ID" in excinfo.value.reason


def test_delete_item_synceditem_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.delete_item_synceditem(MISSING_ITEM_ID, MISSING_ITEM_ID)
    assert excinfo.value.status_code == 404


def test_put_items_tree_location(items_api, scratch_item):
    source_parent = scratch_item.create("source-parent")
    target_parent = scratch_item.create("target-parent")
    child = scratch_item.create("child", source_parent)
    assert items_api.get_item_location(child).data["parent"] == {"item": source_parent}

    assert items_api.put_items_tree_location([child], target_parent) == 200

    assert items_api.get_item_location(child).data["parent"] == {"item": target_parent}
    assert items_api.get_item_children(source_parent).data == []
    assert [item["id"] for item in items_api.get_item_children(target_parent).data] == [
        child
    ]


def test_put_items_tree_location_insert_before(items_api, scratch_item):
    source_parent = scratch_item.create("source-parent")
    target_parent = scratch_item.create("target-parent")
    first = scratch_item.create("first", target_parent)
    second = scratch_item.create("second", target_parent)
    moved = [scratch_item.create("moved-a", source_parent)]
    moved.append(scratch_item.create("moved-b", source_parent))

    assert items_api.put_items_tree_location(moved, target_parent, second) == 200

    children = items_api.get_item_children(target_parent).data
    # The server places a batch of moved items in reverse order.
    assert [item["id"] for item in children] == [first, *reversed(moved), second]


def test_put_items_tree_location_unknown_parent(items_api, scratch_item):
    parent = scratch_item.create("parent")
    child = scratch_item.create("child", parent)
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.put_items_tree_location([child], MISSING_ITEM_ID)
    assert excinfo.value.status_code == 404
    assert items_api.get_item_location(child).data["parent"] == {"item": parent}


def test_put_item_location_within_project_is_refused(
    items_api, scratch_item, real_project
):
    parent = scratch_item.create("parent")
    child = scratch_item.create("child", parent)
    with pytest.raises(APIClientException) as excinfo:
        items_api.put_item_location(child, {"project": real_project})
    assert excinfo.value.status_code == 400
    assert excinfo.value.reason
    assert "between projects" in excinfo.value.reason
    assert items_api.get_item_location(child).data["parent"] == {"item": parent}


def test_post_item_duplicate(items_api, scratch_item):
    parent = scratch_item.create("parent")
    original = scratch_item.create("original", parent)

    response = items_api.post_item_duplicate(original)

    duplicate = response.meta["id"]
    scratch_item.track(duplicate)
    assert response.meta["status"] == "Created"
    assert duplicate != original
    copy = items_api.get_item(duplicate).data
    original_name = items_api.get_item(original).data["fields"]["name"]
    assert copy["fields"]["name"] == f"Duplicate of {original_name}"
    assert copy["location"]["parent"] == {"item": parent}
    assert items_api.get_item_tags(duplicate).data == []


def test_post_item_duplicate_include_tags(items_api, scratch_item, real_tag):
    original = scratch_item.create("original")
    items_api.post_item_tag(original, real_tag)

    response = items_api.post_item_duplicate(original, include_tags=True)

    duplicate = response.meta["id"]
    scratch_item.track(duplicate)
    assert real_tag in {tag["id"] for tag in items_api.get_item_tags(duplicate).data}


def test_post_item_duplicate_item_with_children(items_api, scratch_item):
    parent = scratch_item.create("parent")
    scratch_item.create("child", parent)
    try:
        items_api.post_item_duplicate(parent)
    except APIServerException as error:
        assert error.status_code == 500
    else:
        pytest.fail("duplicating an item with children was expected to fail")


def test_post_item_duplicate_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.post_item_duplicate(MISSING_ITEM_ID)
    assert excinfo.value.status_code == 404


def description_patch(item_ids, text):
    return [
        {
            "items": item_ids,
            "operations": [
                {"op": "replace", "path": "/fields/description", "value": text}
            ],
        }
    ]


def test_patch_items(items_api, scratch_item):
    item_ids = [scratch_item.create("first"), scratch_item.create("second")]

    assert items_api.patch_items(description_patch(item_ids, "zz-char-patched")) == 200

    def patched():
        return all(
            items_api.get_item(item_id).data["fields"].get("description")
            == "zz-char-patched"
            for item_id in item_ids
        )

    assert wait_for(patched)


def test_patch_items_unknown_item(items_api, scratch_item):
    item_id = scratch_item.create()
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.patch_items(description_patch([item_id, MISSING_ITEM_ID], "x"))
    assert excinfo.value.status_code == 404
    # The 404 is synchronous validation: the valid item is not patched.
    assert items_api.get_item(item_id).data["fields"].get("description") is None


def test_patch_items_empty_list(items_api):
    with pytest.raises(APIClientException) as excinfo:
        items_api.patch_items([])
    assert excinfo.value.status_code == 400
    assert excinfo.value.reason
    assert "empty list" in excinfo.value.reason


def test_post_item_location_naming_item_and_project_is_ambiguous(
    items_api, scratch_item, real_project, real_item_type, real_abstract_item
):
    try:
        response = items_api.post_item(
            real_project,
            real_item_type,
            real_item_type,
            {"item": real_abstract_item, "project": real_project},
            {"name": "zz-char-ambiguous-location", "status": scratch_item.status},
        )
    except APIClientException as error:
        assert error.status_code == 400
        assert error.reason
        assert "ambiguous" in error.reason
    else:
        scratch_item.track(response.meta["id"])
        pytest.fail("an ambiguous parent location was expected to be refused")


def test_put_item(
    items_api, scratch_item, real_project, real_item_type, real_abstract_item
):
    item_id = scratch_item.create()
    name = "zz-char-test_put_item-renamed"

    status = items_api.put_item(
        real_project,
        item_id,
        real_item_type,
        real_item_type,
        {"item": real_abstract_item},
        {"name": name, "status": scratch_item.status, "description": "zz-char-put"},
    )

    assert status == 200
    item = items_api.get_item(item_id).data
    assert item["id"] == item_id
    assert item["fields"]["name"] == name
    assert item["fields"]["description"] == "zz-char-put"
    assert item["version"] > 1


def test_put_item_unknown_item(
    items_api, real_project, real_item_type, real_abstract_item
):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.put_item(
            real_project,
            MISSING_ITEM_ID,
            real_item_type,
            real_item_type,
            {"item": real_abstract_item},
            {"name": "zz-char-put-unknown"},
        )
    assert excinfo.value.status_code == 404


def test_put_item_lock(items_api, scratch_item):
    item_id = scratch_item.create()
    assert items_api.get_item_lock(item_id).data["locked"] is False
    try:
        assert items_api.put_item_lock(item_id, True) == 200
        lock = items_api.get_item_lock(item_id).data
        assert lock["locked"] is True
        assert {"lockedBy", "lastLockedDate"} <= set(lock)
    finally:
        items_api.put_item_lock(item_id, False)
    assert items_api.get_item_lock(item_id).data["locked"] is False


def test_put_item_lock_unknown_item(items_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        items_api.put_item_lock(MISSING_ITEM_ID, True)
    assert excinfo.value.status_code == 404


def test_item_attachment_link_round_trip(
    items_api, scratch_item, real_scratch_attachment
):
    item_id = scratch_item.create()
    linked = False
    try:
        status = items_api.post_item_attachment(item_id, real_scratch_attachment)
        linked = True
        assert status == 201
        attached = items_api.get_item_attachments(item_id).data
        assert [a["id"] for a in attached] == [real_scratch_attachment]
        status = items_api.delete_item_attachment(item_id, real_scratch_attachment)
        linked = status != 204
        assert status == 204
        assert items_api.get_item_attachments(item_id).data == []
    finally:
        if linked:
            try:
                items_api.delete_item_attachment(item_id, real_scratch_attachment)
            except Exception as error:  # noqa: BLE001
                warnings.warn(f"could not unlink the scratch attachment: {error}")


def test_post_item_workflow_transition_synthetic(items_api):
    response = items_api.post_item_workflow_transition(5, "101", "Approved")
    assert response.meta["status"] == "Created"


def offline_api(status_code=200):
    client = Mock()
    for verb in ("get", "post", "put", "patch", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text="",
        )
    return ItemsAPI(client), client


def test_delete_methods_return_status_code_and_pass_params():
    api, client = offline_api(204)
    params = {"a": 1}
    assert api.delete_item_tag(5, 6, params=params, timeout=3) == 204
    client.delete.assert_called_with("items/5/tags/6", params=params, timeout=3)
    assert api.delete_item_synceditem(5, 6) == 204
    client.delete.assert_called_with("items/5/synceditems/6", params=None)
    assert api.delete_item_attachment(5, 6) == 204
    client.delete.assert_called_with("items/5/attachments/6", params=None)
    assert params == {"a": 1}


def test_put_methods_send_json_bodies():
    api, client = offline_api()
    params = {"a": 1}
    assert api.put_item_location(5, {"project": 7}, params=params) == 200
    client.put.assert_called_with(
        "items/5/location", params, json={"parent": {"project": 7}}
    )
    assert api.put_items_tree_location([5, 6], 7) == 200
    client.put.assert_called_with(
        "items/treeLocation", None, json={"itemIds": [5, 6], "parentItemId": 7}
    )
    api.put_items_tree_location([5], 7, 8)
    assert client.put.call_args.kwargs["json"] == {
        "itemIds": [5],
        "parentItemId": 7,
        "insertBeforeItemId": 8,
    }
    assert params == {"a": 1}


def test_post_methods_send_json_bodies_and_return_responses():
    api, client = offline_api(201)
    response = api.post_item_duplicate(5, include_tags=True, params={"a": 1})
    client.post.assert_called_with(
        "items/5/duplicate",
        {"a": 1},
        json={"includeTags": True, "includeAttachments": False, "includeLinks": False},
    )
    assert response.data == {}
    api.post_item_workflow_transition(5, "101")
    client.post.assert_called_with(
        "items/5/workflowtransitions", None, json={"transitionId": "101"}
    )
    api.post_item_workflow_transition(5, "101", "Approved")
    assert client.post.call_args.kwargs["json"] == {
        "transitionId": "101",
        "comment": "Approved",
    }


def test_post_item_sends_global_id_and_flags_manual_assignment():
    api, client = offline_api(201)
    api.post_item(7, 24, 24, {"item": 5}, {"name": "a"}, global_id="GID-1")
    args, kwargs = client.post.call_args
    assert args == ("items", {"setGlobalIdManually": True})
    assert kwargs["json"] == {
        "project": 7,
        "itemType": 24,
        "childItemType": 24,
        "location": {"parent": {"item": 5}},
        "fields": {"name": "a"},
        "globalId": "GID-1",
    }


def test_post_item_leaves_caller_params_unchanged():
    api, client = offline_api(201)
    params = {"a": 1}
    api.post_item(7, 24, 24, {"item": 5}, {}, global_id="GID-1", params=params)
    assert client.post.call_args.args[1] == {"a": 1, "setGlobalIdManually": True}
    assert params == {"a": 1}


def test_post_item_without_global_id_sends_no_flag():
    api, client = offline_api(201)
    api.post_item(7, 24, 24, {"item": 5}, {"name": "a"})
    args, kwargs = client.post.call_args
    assert args == ("items", {})
    assert "globalId" not in kwargs["json"]


def test_put_item_sends_json_body_and_returns_status():
    api, client = offline_api()
    params = {"a": 1}
    assert api.put_item(7, 5, 24, 24, {"item": 3}, {"name": "a"}, params=params) == 200
    client.put.assert_called_with(
        "items/5",
        params,
        json={
            "project": 7,
            "itemType": 24,
            "childItemType": 24,
            "location": {"parent": {"item": 3}},
            "fields": {"name": "a"},
        },
    )
    assert params == {"a": 1}


def test_put_item_lock_sends_json_body_and_returns_status():
    api, client = offline_api()
    assert api.put_item_lock(5, True) == 200
    client.put.assert_called_with("items/5/lock", None, json={"locked": True})


def test_post_item_attachment_sends_json_body_and_returns_status():
    api, client = offline_api(201)
    assert api.post_item_attachment(5, 9, params={"a": 1}) == 201
    client.post.assert_called_with(
        "items/5/attachments", {"a": 1}, json={"attachment": 9}
    )


def test_patch_items_sends_json_patches():
    api, client = offline_api()
    patches = description_patch([5], "x")
    assert api.patch_items(patches, params={"a": 1}) == 200
    client.patch.assert_called_with("items", {"a": 1}, json=patches)


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.delete_item_tag(5, 6),
        lambda api: api.delete_item_synceditem(5, 6),
        lambda api: api.delete_item_attachment(5, 6),
        lambda api: api.put_item_location(5, {"project": 7}),
        lambda api: api.put_items_tree_location([5], 7),
        lambda api: api.post_item_duplicate(5),
        lambda api: api.patch_items([]),
        lambda api: api.post_item_workflow_transition(5, "101"),
        lambda api: api.post_item(7, 24, 24, {"item": 5}, {}),
        lambda api: api.post_item(7, 24, 24, {"item": 5}, {}, global_id="G"),
        lambda api: api.post_item_tag(5, 6),
        lambda api: api.post_item_sync(5, 6, params=None),
        lambda api: api.post_item_attachment(5, 9),
        lambda api: api.put_item(7, 5, 24, 24, {"item": 3}, {}),
        lambda api: api.patch_item(5, []),
        lambda api: api.delete_item(5),
        lambda api: api.put_item_lock(5, True),
    ],
    ids=[
        "delete_tag",
        "delete_synceditem",
        "delete_attachment",
        "put_location",
        "put_tree_location",
        "duplicate",
        "patch_items",
        "workflow_transition",
        "post_item",
        "post_item_global_id",
        "post_tag",
        "post_sync",
        "post_attachment",
        "put_item",
        "patch_item",
        "delete_item",
        "put_lock",
    ],
)
def test_new_methods_wrap_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "post", "put", "patch", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_patch_item_merges_caller_headers_with_accept():
    api, client = offline_api()
    caller = {"x-custom": "1"}
    api.patch_item(5, [], headers=caller)
    assert client.patch.call_args.kwargs["headers"] == {
        "Accept": "application/json",
        "x-custom": "1",
    }
    assert caller == {"x-custom": "1"}


def test_patch_item_accepts_headers_none():
    api, client = offline_api()
    api.patch_item(5, [], headers=None)
    assert client.patch.call_args.kwargs["headers"] == {"Accept": "application/json"}


def test_put_item_maps_global_id_and_set_global_id_manually():
    api, client = offline_api()
    params = {"setGlobalIdManually": False}
    api.put_item(
        1,
        2,
        3,
        4,
        {"item": 5},
        {"name": "n"},
        params=params,
        set_global_id_manually=True,
        global_id="GID-1",
    )
    args, kwargs = client.put.call_args
    assert args == ("items/2", {"setGlobalIdManually": True})
    assert kwargs["json"]["globalId"] == "GID-1"
    assert params == {"setGlobalIdManually": False}


def test_put_item_sends_nothing_new_by_default():
    api, client = offline_api()
    params = {"a": 1}
    api.put_item(1, 2, 3, 4, {"item": 5}, {"name": "n"}, params=params)
    args, kwargs = client.put.call_args
    assert args[1] is params
    assert "globalId" not in kwargs["json"]


def test_patch_item_maps_return_item():
    api, client = offline_api()
    client.patch.return_value.json.return_value = {"data": {"id": 2}, "meta": {}}
    params = {"returnItem": False}
    response = api.patch_item(2, [], params=params, return_item=True)
    assert client.patch.call_args.args == ("items/2", {"returnItem": True})
    assert response.data == {"id": 2}
    assert params == {"returnItem": False}
    assert api.patch_item(2, [], params=params) == 200
    assert client.patch.call_args.args[1] is params


def test_post_item_duplicate_sends_include_all_fields_and_categories():
    api, client = offline_api()
    api.post_item_duplicate(2, include_all_fields=True, include_categories=False)
    body = client.post.call_args.kwargs["json"]
    assert body["includeAllFields"] is True
    assert body["includeCategories"] is False


def test_post_item_duplicate_leaves_new_fields_out_when_none():
    api, client = offline_api()
    api.post_item_duplicate(2)
    body = client.post.call_args.kwargs["json"]
    assert "includeAllFields" not in body
    assert "includeCategories" not in body


@pytest.mark.parametrize(
    ("method", "args", "verb"),
    [
        ("delete_item", (1,), "delete"),
        ("put_item_lock", (1, True), "put"),
    ],
)
def test_item_writes_pass_kwargs_to_the_client(method, args, verb):
    client = Mock()
    getattr(client, verb).return_value.status_code = 200
    getattr(ItemsAPI(client), method)(*args, timeout=3, headers={"x-custom": "1"})
    kwargs = getattr(client, verb).call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}


def test_put_item_lock_forwards_params_and_kwargs():
    client = Mock()
    client.put.return_value.status_code = 200
    assert ItemsAPI(client).put_item_lock(5, True, params={"a": 1}, timeout=3) == 200
    client.put.assert_called_with(
        "items/5/lock", {"a": 1}, json={"locked": True}, timeout=3
    )


def test_patch_item_caller_header_overrides_case_insensitively():
    client = Mock()
    client.patch.return_value.status_code = 200
    ItemsAPI(client).patch_item(5, [], headers={"accept": "application/xml"})
    headers = client.patch.call_args.kwargs["headers"]
    assert headers.get_list("accept") == ["application/xml"]
