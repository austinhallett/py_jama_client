import logging
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from unittest.mock import Mock

import pytest

from py_jama_client.client import JamaClient, bound_retry_after
from py_jama_client.constants import (
    DEFAULT_RETRY_AFTER_SECONDS,
    MAX_RETRY_AFTER_SECONDS,
    MAX_THROTTLE_WAITS,
    MIN_RETRY_AFTER_SECONDS,
)
from py_jama_client.exceptions import TooManyRequestsException, _parse_retry_after
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


def test_parse_retry_after_parses_delta_and_http_date_values():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    future = format_datetime(now + timedelta(seconds=27), usegmt=True)
    past = format_datetime(now - timedelta(seconds=27), usegmt=True)

    assert _parse_retry_after("17", now) == 17.0
    assert _parse_retry_after(future, now) == 27.0
    assert _parse_retry_after(past, now) == 0.0
    assert _parse_retry_after("invalid", now) is None
    assert _parse_retry_after(None, now) is None


def test_too_many_requests_exception_includes_response_headers():
    response = Mock(
        status_code=429,
        text='{"meta": {"message": "rate limited"}}',
        headers={"Retry-After": "17"},
    )

    with pytest.raises(TooManyRequestsException) as exc_info:
        JamaClient.handle_response_status(response)

    assert exc_info.value.headers
    assert exc_info.value.headers["Retry-After"] == "17"
    assert exc_info.value.retry_after == 17.0


def test_too_many_requests_exception_retry_after_parses_header():
    def throttled(headers):
        return TooManyRequestsException("throttled", headers=headers)

    retry_at = datetime.now(UTC) + timedelta(minutes=1)
    retried_at = datetime.now(UTC) - timedelta(minutes=1)

    assert throttled({"Retry-After": "17"}).retry_after == 17.0
    assert throttled({"retry-after": "17"}).retry_after == 17.0
    future_wait = throttled(
        {"Retry-After": format_datetime(retry_at, usegmt=True)}
    ).retry_after
    assert future_wait is not None
    assert 50 < future_wait <= 60
    assert (
        throttled({"Retry-After": format_datetime(retried_at, usegmt=True)}).retry_after
        == 0.0
    )


def test_too_many_requests_exception_retry_after_is_fixed_when_raised(monkeypatch):
    retry_at = datetime.now(UTC) + timedelta(minutes=1)
    throttled = TooManyRequestsException(
        "throttled", headers={"Retry-After": format_datetime(retry_at, usegmt=True)}
    )
    later = datetime.now(UTC) + timedelta(seconds=30)

    class LaterDatetime:
        @staticmethod
        def now(tz=None):
            return later

    monkeypatch.setattr("py_jama_client.exceptions.datetime", LaterDatetime)

    retry_after = throttled.retry_after
    assert retry_after is not None
    assert 50 < retry_after <= 60


def test_too_many_requests_exception_retry_after_ignores_later_header_changes():
    headers = {"Retry-After": "17"}
    throttled = TooManyRequestsException("throttled", headers=headers)
    headers["Retry-After"] = "99"
    throttled.headers = {"Retry-After": "42"}

    assert throttled.retry_after == 17.0


def test_too_many_requests_exception_retry_after_is_assignable():
    throttled = TooManyRequestsException("throttled", headers={"Retry-After": "17"})
    throttled.retry_after = 3.0
    assert throttled.retry_after == 3.0


def test_too_many_requests_exception_measures_retry_after_from_server_date(
    monkeypatch,
):
    server_now = datetime(2026, 1, 1, tzinfo=UTC)
    headers = {
        "Date": format_datetime(server_now, usegmt=True),
        "Retry-After": format_datetime(server_now + timedelta(seconds=20), usegmt=True),
    }

    class SkewedDatetime:
        @staticmethod
        def now(tz=None):
            return server_now + timedelta(minutes=5)

    monkeypatch.setattr("py_jama_client.exceptions.datetime", SkewedDatetime)

    throttled = TooManyRequestsException("throttled", headers=headers)
    assert throttled.retry_after == 20.0


def test_too_many_requests_exception_uses_local_clock_with_unusable_date():
    retry_at = datetime.now(UTC) + timedelta(minutes=1)
    throttled = TooManyRequestsException(
        "throttled",
        headers={
            "Date": "not a date",
            "Retry-After": format_datetime(retry_at, usegmt=True),
        },
    )

    assert throttled.retry_after is not None
    assert 50 < throttled.retry_after <= 60


def test_bound_retry_after_clamps_to_min_and_max(caplog):
    assert bound_retry_after(0.0) == MIN_RETRY_AFTER_SECONDS
    assert bound_retry_after(42.0) == 42.0
    with caplog.at_level(logging.WARNING, logger="py_jama_client"):
        assert bound_retry_after(MAX_RETRY_AFTER_SECONDS + 1) == MAX_RETRY_AFTER_SECONDS
    assert "Retry-After" in caplog.text


def test_bound_retry_after_defaults_without_retry_after():
    assert bound_retry_after(None) == DEFAULT_RETRY_AFTER_SECONDS


def test_too_many_requests_exception_retry_after_is_none_without_usable_header():
    assert TooManyRequestsException("throttled").retry_after is None
    assert TooManyRequestsException("throttled", headers={}).retry_after is None
    assert (
        TooManyRequestsException(
            "throttled", headers={"Retry-After": "invalid"}
        ).retry_after
        is None
    )
    assert (
        TooManyRequestsException(
            "throttled", headers={"Retry-After": "nan"}
        ).retry_after
        is None
    )


def test_get_all_honors_retry_after(monkeypatch, caplog):
    client = JamaClient.__new__(JamaClient)
    # Kept above the default so a fallback to it cannot pass the test
    expected_wait = DEFAULT_RETRY_AFTER_SECONDS + 60
    retry_at = datetime.now(UTC) + timedelta(seconds=expected_wait)
    throttled = TooManyRequestsException(
        "throttled", headers={"Retry-After": format_datetime(retry_at, usegmt=True)}
    )
    client.get_page = Mock(
        side_effect=[
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
        ]
    )
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)

    caplog.set_level(logging.INFO, logger="py_jama_client")
    response = client.get_all("items", params={}, allowed_results_per_page=2)

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.args[1] for call in client.get_page.call_args_list] == [0, 2, 2]
    sleep.assert_called_once()
    assert expected_wait - 10 < sleep.call_args.args[0] <= expected_wait
    assert "Throttled" in caplog.text


def test_get_all_stops_after_max_consecutive_throttles(monkeypatch):
    client = JamaClient.__new__(JamaClient)
    client.get_page = Mock(
        side_effect=[
            TooManyRequestsException("throttled") for _ in range(MAX_THROTTLE_WAITS + 1)
        ]
    )
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)

    with pytest.raises(TooManyRequestsException):
        client.get_all("items", allowed_results_per_page=2)

    assert client.get_page.call_count == MAX_THROTTLE_WAITS + 1
    assert sleep.call_count == MAX_THROTTLE_WAITS


def test_get_all_merges_linked_data_across_pages():
    client = JamaClient.__new__(JamaClient)
    client.get_page = Mock(
        side_effect=[
            ClientResponse(
                {"pageInfo": {"startIndex": 0, "totalResults": 2}},
                {},
                {"items": {1: {"id": 1, "name": "first"}, 2: {"id": 2}}},
                [{"id": 1}],
            ),
            ClientResponse(
                {"pageInfo": {"startIndex": 1, "totalResults": 2}},
                {},
                {"items": {1: {"id": 1, "name": "updated"}, 3: {"id": 3}}},
                [{"id": 2}],
            ),
        ]
    )

    response = client.get_all("items", allowed_results_per_page=1)

    assert response.linked == {
        "items": {
            1: {"id": 1, "name": "updated"},
            2: {"id": 2},
            3: {"id": 3},
        }
    }


def test_get_page_does_not_mutate_params():
    client = JamaClient.__new__(JamaClient)
    response = Mock(status_code=200)
    response.json.return_value = {"meta": {}, "links": {}, "linked": {}, "data": []}
    client.get = Mock(return_value=response)
    params = {"project": 1}

    client.get_page("items", 10, params=params, allowed_results_per_page=5)

    assert params == {"project": 1}
    assert client.get.call_args.kwargs["params"] == {
        "project": 1,
        "startAt": 10,
        "maxResults": 5,
    }
