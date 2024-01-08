import os
from py_jama_client.core import Core, AsyncCore
from py_jama_client.client import JamaClient


def test_client_creation():
    client = JamaClient(
        core=Core(
            host=os.getenv("HOST"),
            credentials=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")),
            verify=False,
            oauth=True,
        )
    )
    response = client.get_baselines(project_id=82)
    assert response is not None
