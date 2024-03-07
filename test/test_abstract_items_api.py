from py_jama_client.apis.abstract_items_api import AbstractItemsAPI


def test_get_abstract_item(get_test_jama_client):
    abstract_items_api = AbstractItemsAPI(get_test_jama_client)
    response = abstract_items_api.get_abstract_items(project=(195,), item_type=(193,))
    assert response.data != []
