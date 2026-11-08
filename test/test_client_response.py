from unittest.mock import Mock

import pytest

from py_jama_client.client import JamaClient
from py_jama_client.constants import MAX_THROTTLE_WAITS
from py_jama_client.exceptions import TooManyRequestsException
from py_jama_client.response import ClientResponse


def test_client_response(get_example_client_response):
    assert "pageInfo" in get_example_client_response.meta


def test_client_to_dict(get_example_client_response):
    assert "pageInfo" in get_example_client_response.to_dict()["meta"]


def test_client_combination(get_example_client_response):
    new_response = ClientResponse(
        meta={"new": "meta"},
        links={"new": "links"},
        linked={"new": "linked"},
        data=[{"id": 1}],
    )
    combined_response = get_example_client_response + new_response
    assert "pageInfo" in combined_response.meta
    assert "new" in combined_response.meta
    assert "data" in combined_response.to_dict()
    assert len(combined_response.data) == 3
    assert combined_response.data[0]["id"] == 50621
    assert combined_response.data[2]["id"] == 1


def test_too_many_requests_exception_includes_response_headers():
    response = Mock(
        status_code=429,
        text='{"meta": {"message": "rate limited"}}',
        headers={"Retry-After": "17"},
    )

    with pytest.raises(TooManyRequestsException) as exc_info:
        JamaClient.handle_response_status(response)

    assert exc_info.value.headers["Retry-After"] == "17"


def test_get_all_honors_retry_after(monkeypatch):
    client = JamaClient.__new__(JamaClient)
    throttled = TooManyRequestsException("throttled")
    throttled.headers = {"Retry-After": "17"}
    client.get_page = Mock(side_effect=[
        ClientResponse(
            {"pageInfo": {"startIndex": 0, "totalResults": 3}},
            {},
            {},
            [{"id": 1}, {"id": 2}],
        ),
        throttled,
        ClientResponse(
            {"pageInfo": {"startIndex": 2, "totalResults": 3}},
            {},
            {},
            [{"id": 3}],
        ),
    ])
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)

    response = client.get_all(
        "items", params={}, allowed_results_per_page=2
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.args[1] for call in client.get_page.call_args_list] == [
        0, 2, 2
    ]
    sleep.assert_called_once_with(17.0)


def test_get_all_stops_after_max_consecutive_throttles(monkeypatch):
    client = JamaClient.__new__(JamaClient)
    client.get_page = Mock(side_effect=[
        TooManyRequestsException("throttled")
        for _ in range(MAX_THROTTLE_WAITS + 1)
    ])
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)

    with pytest.raises(TooManyRequestsException):
        client.get_all("items", allowed_results_per_page=2)

    assert client.get_page.call_count == MAX_THROTTLE_WAITS + 1
    assert sleep.call_count == MAX_THROTTLE_WAITS
