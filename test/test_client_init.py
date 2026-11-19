import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from unittest.mock import Mock

import httpx
import pytest

from py_jama_client.client import JamaClient
from py_jama_client.exceptions import UnauthorizedTokenException


def test_client_creation(get_test_jama_client):
    client = get_test_jama_client
    assert isinstance(client, JamaClient)


def test_oauth_token_is_fetched_when_missing():
    client = JamaClient.__new__(JamaClient)
    client._oauth_token_lock = Lock()
    client._token = None
    refresh = Mock()
    client._get_fresh_token = refresh

    client._check_oauth_token()

    refresh.assert_called_once_with()


def test_concurrent_oauth_requests_refresh_token_once():
    client = JamaClient.__new__(JamaClient)
    client._oauth_token_lock = Lock()
    client._token = "expired"
    client._token_acquired_at = 0
    client._token_expires_in = 1

    def refresh_token():
        time.sleep(0.01)
        client._token = "fresh"
        client._token_acquired_at = int(time.time())
        client._token_expires_in = 3600

    refresh = Mock(side_effect=refresh_token)
    client._get_fresh_token = refresh
    check_oauth_token = client._check_oauth_token

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: check_oauth_token(), range(8)))

    refresh.assert_called_once_with()


def test_fresh_token_raises_on_unexpected_success_status(monkeypatch):
    client = JamaClient.__new__(JamaClient)
    client._token = None
    client._token_host = "https://jama.invalid/rest/oauth/token"
    client._credentials = ("id", "secret")
    client._verify = True
    request = httpx.Request("POST", client._token_host)
    monkeypatch.setattr(
        httpx, "post", Mock(return_value=httpx.Response(204, request=request))
    )

    with pytest.raises(UnauthorizedTokenException):
        client._get_fresh_token()


@pytest.mark.parametrize(
    "body",
    [b"<html>maintenance</html>", b'{"error": "invalid_client"}'],
)
def test_fresh_token_raises_on_unusable_success_body(monkeypatch, body):
    client = JamaClient.__new__(JamaClient)
    client._token = None
    client._token_host = "https://jama.invalid/rest/oauth/token"
    client._credentials = ("id", "secret")
    client._verify = True
    request = httpx.Request("POST", client._token_host)
    monkeypatch.setattr(
        httpx,
        "post",
        Mock(return_value=httpx.Response(200, content=body, request=request)),
    )

    with pytest.raises(UnauthorizedTokenException):
        client._get_fresh_token()
