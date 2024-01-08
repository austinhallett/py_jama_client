import os
import pytest


@pytest.fixture(autouse=True)
def env_vars():
    if os.getenv("CLIENT_ID") is None and os.getenv("CLIENT_SECRET") is None:
        raise ValueError(
            """
                Please set environment variables 'client_id' and 'client_secret' 
                to run tests properly.
            """
        )
