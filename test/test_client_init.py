import os
from py_jama_client.client import BaseClient


def test_client_creation(get_test_jama_client):
    client = get_test_jama_client
    assert isinstance(client, BaseClient)
