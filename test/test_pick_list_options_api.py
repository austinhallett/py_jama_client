from unittest.mock import Mock

import pytest

from py_jama_client.apis.item_types_api import ItemTypesAPI
from py_jama_client.apis.pick_list_options_api import PickListOptionsAPI
from py_jama_client.apis.pick_lists_api import PickListsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_OPTION_ID = 2147483647

OPTION = {
    "name": "Example option",
    "description": "Example description",
    "value": "example",
    "color": "#336699",
    "sortOrder": 1,
    "infotip": "Example infotip",
    "default": False,
}


@pytest.fixture(scope="function")
def pick_list_options_api(get_test_jama_client, bounded_pages):
    return PickListOptionsAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def status_option(get_test_jama_client, real_item_type):
    fields = (
        ItemTypesAPI(get_test_jama_client).get_item_type(real_item_type).data["fields"]
    )
    for field in fields:
        if field["name"] == "status" and field.get("pickList"):
            pick_list = field["pickList"]
            break
    else:
        pytest.fail("The fixture item type has no status pick list.")
    options = PickListsAPI(get_test_jama_client).get_pick_list_options(
        pick_list, allowed_results_per_page=5
    )
    assert options.data
    return pick_list, options.data[0]


def test_get_pick_list_option(pick_list_options_api, status_option):
    pick_list, option = status_option
    response = pick_list_options_api.get_pick_list_option(option["id"])
    assert response.data["id"] == option["id"]
    assert response.data["pickList"] == pick_list
    assert response.data["name"] == option["name"]
    assert response.data["type"] == "picklistoptions"


def test_get_pick_list_option_missing_option(pick_list_options_api):
    with pytest.raises(ResourceNotFoundException):
        pick_list_options_api.get_pick_list_option(MISSING_OPTION_ID)


def test_get_pick_list_option_wraps_core_exception():
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        PickListOptionsAPI(client).get_pick_list_option(1)


def test_put_pick_list_option_docs(pick_list_options_api):
    # The docs give no example request body, only the RequestPickListOption model.
    assert pick_list_options_api.put_pick_list_option(6, OPTION) == 200


def offline_api():
    client = Mock()
    client.put.return_value = Mock(
        status_code=200, json=Mock(return_value={"meta": {}}), text=""
    )
    return PickListOptionsAPI(client), client


def test_put_pick_list_option_forwards_params_untouched():
    api, client = offline_api()
    params = {"a": 1}
    api.put_pick_list_option(6, OPTION, params=params)
    assert client.put.call_args.args[1] == {"a": 1}
    assert params == {"a": 1}


def test_put_pick_list_option_wraps_core_exception():
    api, client = offline_api()
    client.put.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        api.put_pick_list_option(6, OPTION)


def test_get_pick_list_option_passes_kwargs_to_the_client():
    client = Mock()
    client.get.return_value.status_code = 200
    PickListOptionsAPI(client).get_pick_list_option(
        1, timeout=3, headers={"x-custom": "1"}
    )
    kwargs = client.get.call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
