import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from unittest.mock import Mock

from py_jama_client.client import JamaClient


def test_client_creation(get_test_jama_client):
    client = get_test_jama_client
    assert isinstance(client, JamaClient)


def test_oauth_token_is_fetched_when_missing():
    client = JamaClient.__new__(JamaClient)
    client._JamaClient__oauth_token_lock = Lock()
    client._JamaClient__token = None
    refresh = Mock()
    client._JamaClient__get_fresh_token = refresh

    client._JamaClient__check_oauth_token()

    refresh.assert_called_once_with()


def test_concurrent_oauth_requests_refresh_token_once():
    client = JamaClient.__new__(JamaClient)
    client._JamaClient__oauth_token_lock = Lock()
    client._JamaClient__token = "expired"
    client._JamaClient__token_acquired_at = 0
    client._JamaClient__token_expires_in = 1

    def refresh_token():
        time.sleep(0.01)
        client._JamaClient__token = "fresh"
        client._JamaClient__token_acquired_at = time.time()
        client._JamaClient__token_expires_in = 3600

    refresh = Mock(side_effect=refresh_token)
    client._JamaClient__get_fresh_token = refresh
    check_oauth_token = client._JamaClient__check_oauth_token

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: check_oauth_token(), range(8)))

    refresh.assert_called_once_with()
