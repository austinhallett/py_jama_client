from unittest.mock import Mock

import pytest

from py_jama_client.apis.item_types_api import ItemTypesAPI
from py_jama_client.exceptions import APIException, CoreException


@pytest.fixture(scope="function")
def item_types_api(get_test_jama_client):
    api_instance = ItemTypesAPI(get_test_jama_client)
    return api_instance


def test_get_item_types(item_types_api, bounded_pages):
    bounded_pages["result_limit"] = 2
    response = item_types_api.get_item_types()
    assert bounded_pages["offset_total"] > 2
    assert len(response.data) == 2
    assert all({"id", "typeKey", "display"} <= set(t) for t in response.data)
    assert {t["type"] for t in response.data} == {"itemtypes"}


def test_get_item_type(item_types_api, real_item_type):
    response = item_types_api.get_item_type(item_type_id=real_item_type)
    assert response.data is not None


def test_post_item_type_docs(item_types_api):
    # The docs give no example request body, only the RequestItemType model.
    response = item_types_api.post_item_type(
        {
            "typeKey": "EXMPL",
            "display": "Example item type",
            "displayPlural": "Example item types",
            "description": "Example description",
            "image": "example-image",
            "category": "CORE",
            "widgets": [{"name": "ACTIVITIES", "synchronize": True}],
        }
    )
    assert response.data == 101
    assert response.meta["status"] == "OK"


def test_post_item_type_field_docs(item_types_api):
    # The docs give no example request body, only the RequestItemTypeField model.
    response = item_types_api.post_item_type_field(
        5,
        {
            "name": "example_field",
            "label": "Example field",
            "fieldType": "INTEGER",
            "readOnly": False,
            "readOnlyAllowApiOverwrite": False,
            "required": False,
            "triggerSuspect": False,
            "synchronize": False,
            "pickList": 1,
            "textType": "TEXTAREA",
            "infotip": "Example infotip",
        },
    )
    assert response.meta["status"] == "OK"
    assert response.data == {}


def offline_api():
    client = Mock()
    client.post.return_value = Mock(
        status_code=201, json=Mock(return_value={"meta": {}}), text=""
    )
    return ItemTypesAPI(client), client


@pytest.mark.parametrize(
    "call",
    [
        lambda api, params: api.post_item_type({"typeKey": "A"}, params=params),
        lambda api, params: api.post_item_type_field(5, {"name": "a"}, params=params),
    ],
    ids=["item_type", "field"],
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
        lambda api: api.post_item_type({}),
        lambda api: api.post_item_type_field(5, {}),
    ],
    ids=["item_type", "field"],
)
def test_admin_posts_wrap_core_exception(call):
    api, client = offline_api()
    client.post.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_get_item_types_passes_params():
    client = Mock()
    ItemTypesAPI(client).get_item_types(params={"maxResults": 3})
    assert client.get_all.call_args.args[1] == {"maxResults": 3}


def test_get_item_type_wraps_core_exception():
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        ItemTypesAPI(client).get_item_type(item_type_id=1)


def test_get_item_type_passes_kwargs_to_the_client():
    client = Mock()
    client.get.return_value.status_code = 200
    ItemTypesAPI(client).get_item_type(1, timeout=3, headers={"x-custom": "1"})
    kwargs = client.get.call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
