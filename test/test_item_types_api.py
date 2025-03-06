from py_jama_client.apis.item_types_api import ItemTypesAPI
import pytest


@pytest.fixture(scope="function")
def item_types_api(get_test_jama_client):
    api_instance = ItemTypesAPI(get_test_jama_client)
    return api_instance


def test_get_item_types(item_types_api):
    response = item_types_api.get_item_types()
    assert response.data != []


def test_get_item_type(item_types_api, real_item_type):
    response = item_types_api.get_item_type(item_type_id=real_item_type)
    assert response.data is not None
