from py_jama_client.apis.abstract_items_api import AbstractItemsAPI
import pytest

@pytest.fixture(scope="function")
def abstract_items_api(get_test_jama_client):
    api_instance = AbstractItemsAPI(get_test_jama_client)
    return api_instance


def test_get_abstract_items(abstract_items_api,
                            real_project,
                            real_item_type):
    response = abstract_items_api.get_abstract_items(
        project=(real_project,),
        item_type=(real_item_type,))
    assert response.data != []


def test_get_abstract_item(abstract_items_api,
                           real_abstract_item):
    response = abstract_items_api.get_abstract_item(item_id=real_abstract_item)
    assert response.data != []


def test_get_abstract_item_versions(abstract_items_api,
                                    real_abstract_item):
    response = abstract_items_api.get_abstract_item_versions(
        item_id=real_abstract_item)
    assert response.data != []

def test_get_abstract_item_version(abstract_items_api,
                                   real_abstract_item,
                                   real_abstract_item_version):
    response = abstract_items_api.get_abstract_item_version(
        item_id=real_abstract_item,
        version_num=real_abstract_item_version)
    assert response.data != []


def test_get_abstract_versioned_item(abstract_items_api,
                                     real_abstract_item,
                                     real_abstract_item_version):
    response = abstract_items_api.get_abstract_versioned_item(
        item_id=real_abstract_item,
        version_num=real_abstract_item_version)
    assert response.data != []
