import base64
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


@pytest.fixture
def token_client():
    clients = []

    def make(handler):
        client = JamaClient.__new__(JamaClient)
        client._token = None
        client._token_host = "https://jama.invalid/rest/oauth/token"
        client._credentials = ("id", "secret")
        client._session = httpx.Client(transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    yield make
    for client in clients:
        client._session.close()


def test_fresh_token_is_requested_through_session(token_client):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"access_token": "tok", "expires_in": 60})

    client = token_client(handler)

    client._get_fresh_token()

    assert [(r.method, str(r.url)) for r in requests] == [
        ("POST", "https://jama.invalid/rest/oauth/token")
    ]
    expected_auth = "Basic " + base64.b64encode(b"id:secret").decode()
    assert requests[0].headers["authorization"] == expected_auth
    assert requests[0].content == b"grant_type=client_credentials"
    assert client._token == "tok"


def test_fresh_token_raises_on_unexpected_success_status(token_client):
    client = token_client(lambda request: httpx.Response(204))

    with pytest.raises(UnauthorizedTokenException):
        client._get_fresh_token()


@pytest.mark.parametrize(
    "body",
    [b"<html>maintenance</html>", b'{"error": "invalid_client"}'],
)
def test_fresh_token_raises_on_unusable_success_body(token_client, body):
    client = token_client(lambda request: httpx.Response(200, content=body))

    with pytest.raises(UnauthorizedTokenException):
        client._get_fresh_token()


def test_session_closed_when_initial_token_fetch_fails(monkeypatch):
    sessions = []

    def session_class(**kwargs):
        session = httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(401)),
            **kwargs,
        )
        sessions.append(session)
        return session

    monkeypatch.setattr(JamaClient, "session_class", staticmethod(session_class))

    with pytest.raises(UnauthorizedTokenException):
        JamaClient("https://jama.invalid", ("id", "secret"), oauth=True)

    assert len(sessions) == 1
    assert sessions[0].is_closed


def test_delete_with_body_sends_json_with_basic_auth(token_client):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200)

    client = token_client(handler)
    client._oauth = False
    client._host_name = "https://jama.invalid/rest/v1/"

    response = client.delete_with_body(
        "items/5/categories", {"categoryPathIds": [4]}, params={"a": "1"}
    )

    assert response.status_code == 200
    assert (requests[0].method, str(requests[0].url)) == (
        "DELETE",
        "https://jama.invalid/rest/v1/items/5/categories?a=1",
    )
    assert requests[0].content == b'{"categoryPathIds":[4]}'
    assert requests[0].headers["content-type"] == "application/json"
    expected_auth = "Basic " + base64.b64encode(b"id:secret").decode()
    assert requests[0].headers["authorization"] == expected_auth


def test_delete_with_body_sends_token_and_keeps_extra_headers_with_oauth(
    token_client,
):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200)

    client = token_client(handler)
    client._oauth = True
    client._host_name = "https://jama.invalid/rest/v1/"
    client._token = "tok-123"
    client._token_acquired_at = int(time.time())
    client._token_expires_in = 3600
    client._oauth_token_lock = Lock()
    expected_auth = client._add_auth_header()["Authorization"]

    client.delete_with_body(
        "items/5/categories",
        {"categoryPathIds": [4]},
        headers={"X-Extra": "kept"},
    )

    assert requests[0].method == "DELETE"
    assert expected_auth.endswith("tok-123")
    assert requests[0].headers["authorization"] == expected_auth
    assert requests[0].headers["x-extra"] == "kept"
    assert requests[0].content == b'{"categoryPathIds":[4]}'
