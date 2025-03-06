from py_jama_client.client import JamaClient


def test_client_creation(get_test_jama_client):
    client = get_test_jama_client
    assert isinstance(client, JamaClient)
