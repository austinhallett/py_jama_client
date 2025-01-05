from py_jama_client.apis.item_types_api import ItemTypesAPI


def test_get_item_types(get_test_jama_client):
    item_types_api = ItemTypesAPI(get_test_jama_client)
    response = item_types_api.get_item_types()
    assert response.data != []


def test_get_tag(get_test_jama_client):
    item_types_api = ItemTypesAPI(get_test_jama_client)
    response = item_types_api.get_item_type(item_type_id=1)
    assert response.data is not None
