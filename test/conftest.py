import os
import pytest
from py_jama_client.client import BaseClient


@pytest.fixture(autouse=True)
def env_vars():
    if os.getenv("CLIENT_ID") is None and os.getenv("CLIENT_SECRET") is None:
        raise ValueError(
            """
                Please set environment variables 'client_id' and 'client_secret' 
                to run tests properly.
            """
        )


@pytest.fixture(scope="session")
def get_test_jama_client():
    client = BaseClient(
        host=os.getenv("HOST"),
        credentials=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")),
        verify=False,
        oauth=True,
    )

    yield client
