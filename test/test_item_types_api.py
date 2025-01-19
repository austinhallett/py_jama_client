from py_jama_client.apis.item_types_api import ItemTypesAPI


def test_get_item_types(get_test_jama_client):
    item_types_api = ItemTypesAPI(get_test_jama_client)
    response = item_types_api.get_item_types()
    assert response.data != []


def test_get_item_type(get_test_jama_client, real_item_type):
    item_types_api = ItemTypesAPI(get_test_jama_client)
    response = item_types_api.get_item_type(item_type_id=real_item_type)
    assert response.data is not None
