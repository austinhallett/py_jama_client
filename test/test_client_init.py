import os
from py_jama_client.core import Core
from py_jama_client.client import JamaClient, BaseClient


def test_client_creation():
    client = JamaClient(
        core=Core(
            host=os.getenv("HOST"),
            credentials=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")),
            verify=False,
            oauth=True,
        )
    )
    assert isinstance(client, BaseClient)
