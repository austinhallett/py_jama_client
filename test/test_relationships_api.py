from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import Mock

import pytest

from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.constants import MAX_THROTTLE_WAITS
from py_jama_client.exceptions import TooManyRequestsException
from py_jama_client.response import ClientResponse


@pytest.fixture(scope="function")
def relationships_api(get_test_jama_client, bounded_live_pages):
    api_instance = RelationshipsAPI(get_test_jama_client)
    return api_instance


def test_get_relationships(relationships_api, real_project, bounded_live_pages):
    response = relationships_api.get_relationships(project_id=real_project)
    if len(response.data) < 12:
        pytest.skip("The sample project has fewer than 12 relationships.")
    assert len(response.data) == 12
    page_sizes = (bounded_live_pages["last_id"] or
                  bounded_live_pages["offset"])
    assert page_sizes == [5, 5, 2]


def test_get_all_lastid(relationships_api, real_project, bounded_live_pages):
    resource_path = "relationships"
    params = {"project": real_project,
              "maxResults": 1}
    response = relationships_api.client.get(resource_path, params=params)
    if (response.status_code == 400 and
            "lastId parameter is now required" in response.text):
        response = relationships_api.get_all_lastid(
            resource_path=resource_path,
            params={"project": real_project},
            allowed_results_per_page=5)
    else:
        pytest.skip("lastId parameter is not required by test Jama instance.")
    if len(response.data) < 12:
        pytest.skip("The sample project has fewer than 12 relationships.")
    assert len(response.data) == 12
    assert bounded_live_pages["last_id"] == [5, 5, 2]


def test_get_all_lastid_ignores_zero_total_results_when_page_has_data():
    api = RelationshipsAPI(Mock())
    api.get_page_lastid = Mock(side_effect=[
        ClientResponse(
            {"pageInfo": {"startIndex": 0, "totalResults": 0}},
            {},
            {},
            [{"id": 1}, {"id": 2}],
        ),
        ClientResponse(
            {"pageInfo": {"startIndex": 2, "totalResults": 0}},
            {},
            {},
            [{"id": 3}],
        ),
    ])

    response = api.get_all_lastid(
        "relationships",
        params={"project": 1, "omitCount": "true"},
        allowed_results_per_page=2,
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert response.meta["pageInfo"]["totalResults"] == 3
    assert [call.args[1] for call in api.get_page_lastid.call_args_list] == [
        0, 2
    ]


def test_get_all_lastid_merges_linked_data_across_pages():
    api = RelationshipsAPI(Mock())
    api.get_page_lastid = Mock(side_effect=[
        ClientResponse({}, {}, {"items": {1: {"id": 1, "name": "first"},
                                          2: {"id": 2}}},
                       [{"id": 1}, {"id": 2}]),
        ClientResponse({}, {}, {"items": {1: {"id": 1, "name": "updated"},
                                          3: {"id": 3}}},
                       [{"id": 3}]),
    ])

    response = api.get_all_lastid("relationships", allowed_results_per_page=2)

    assert response.linked == {
        "items": {
            1: {"id": 1, "name": "updated"},
            2: {"id": 2},
            3: {"id": 3},
        }
    }


def test_get_page_lastid_does_not_mutate_params():
    api = RelationshipsAPI(Mock())
    response = Mock(status_code=200)
    response.json.return_value = {"meta": {}, "links": {}, "linked": {},
                                  "data": []}
    api.client.get = Mock(return_value=response)
    params = {"project": 1}

    api.get_page_lastid("relationships", 10, params=params,
                        allowed_results_per_page=5)

    assert params == {"project": 1}
    assert api.client.get.call_args.kwargs["params"] == {
        "project": 1, "lastId": 10, "maxResults": 5
    }


def test_get_all_lastid_honors_retry_after(monkeypatch):
    api = RelationshipsAPI(Mock())
    throttled = TooManyRequestsException("throttled")
    retry_at = datetime.now(timezone.utc) + timedelta(minutes=1)
    throttled.headers = {
        "Retry-After": format_datetime(retry_at, usegmt=True)
    }
    api.get_page_lastid = Mock(side_effect=[
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

    response = api.get_all_lastid(
        "relationships", params={"project": 1}, allowed_results_per_page=2
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.args[1] for call in api.get_page_lastid.call_args_list] == [
        0, 2, 2
    ]
    sleep.assert_called_once()
    assert 0 < sleep.call_args.args[0] <= 60


def test_get_all_lastid_stops_after_max_consecutive_throttles(monkeypatch):
    api = RelationshipsAPI(Mock())
    api.get_page_lastid = Mock(side_effect=[
        TooManyRequestsException("throttled")
        for _ in range(MAX_THROTTLE_WAITS + 1)
    ])
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)

    with pytest.raises(TooManyRequestsException):
        api.get_all_lastid("relationships", allowed_results_per_page=2)

    assert api.get_page_lastid.call_count == MAX_THROTTLE_WAITS + 1
    assert sleep.call_count == MAX_THROTTLE_WAITS


def test_get_page_lastid(relationships_api, real_project):
    resource_path = "relationships"
    params = {"project": real_project,
              "maxResults": 1}
    response = relationships_api.client.get(resource_path, params=params)
    if (response.status_code == 400 and
            "lastId parameter is now required" in response.text):
        response = relationships_api.get_page_lastid(
            resource_path=resource_path,
            last_id=0,
            params={"project": real_project})
    else:
        pytest.skip("lastId parameter is not required by test Jama instance.")
    assert response.data != []


def test_get_relationship(relationships_api, real_relationship):
    response = relationships_api.get_relationship(
        relationship_id=real_relationship)
    assert response.data != []


def test_get_relationship_types(relationships_api):
    response = relationships_api.get_relationship_types()
    assert response.data != []


def test_get_relationship_type(relationships_api, real_relationship_type):
    response = relationships_api.get_relationship_type(
        relationship_type_id=real_relationship_type
    )
    assert response.data != []
