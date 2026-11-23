from unittest.mock import Mock

import pytest

from py_jama_client.apis.filters_api import FiltersAPI
from py_jama_client.exceptions import (
    APIClientException,
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_FILTER_ID = 2147483647


@pytest.fixture(scope="function")
def filters_api(get_test_jama_client, bounded_pages):
    return FiltersAPI(get_test_jama_client)


def test_get_filters(filters_api, real_project, bounded_pages):
    response = filters_api.get_filters(params={"project": real_project})
    assert bounded_pages["offset_total"] >= 12
    assert len(response.data) == 12
    assert bounded_pages["offset"] == [5, 5, 2]
    assert all({"id", "name", "projectScope", "type"} <= set(f) for f in response.data)
    assert {f["type"] for f in response.data} == {"filters"}


def test_get_filter(filters_api, real_project, real_filter):
    response = filters_api.get_filter(filter_id=real_filter)
    assert response.data["id"] == real_filter
    assert response.data["type"] == "filters"
    assert response.data["name"]
    assert response.data["projectScope"] == "SPECIFIED"
    assert response.data["specifiedProject"] == real_project


def test_get_filter_missing_filter(filters_api):
    with pytest.raises(ResourceNotFoundException):
        filters_api.get_filter(filter_id=MISSING_FILTER_ID)


def test_get_filter_count(filters_api, real_filter):
    response = filters_api.get_filter_count(filter_id=real_filter)
    assert isinstance(response.data, int)
    assert response.data >= 0


def test_get_filter_count_missing_filter(filters_api):
    with pytest.raises(ResourceNotFoundException):
        filters_api.get_filter_count(filter_id=MISSING_FILTER_ID)


def test_get_filter_count_ignores_project_param(filters_api, real_filter, real_project):
    expected = filters_api.get_filter_count(filter_id=real_filter).data
    response = filters_api.get_filter_count(
        filter_id=real_filter, params={"project": real_project}
    )
    assert response.data == expected


def test_get_filter_results(filters_api, real_filter, real_project):
    response = filters_api.get_filter_results(
        filter_id=real_filter, allowed_results_per_page=5
    )
    assert response.data
    assert all({"id", "project", "itemType"} <= set(i) for i in response.data)
    assert {i["project"] for i in response.data} <= {real_project}


def test_get_filter_results_missing_filter(filters_api):
    with pytest.raises(ResourceNotFoundException):
        filters_api.get_filter_results(filter_id=MISSING_FILTER_ID)


def test_get_filter_results_project_on_specified_filter(
    filters_api, real_filter, real_project
):
    with pytest.raises(APIClientException, match="already specifies a project"):
        filters_api.get_filter_results(filter_id=real_filter, project_id=real_project)


def test_get_filter_results_merges_caller_params():
    client = Mock()
    caller_params = {"include": "data.itemType"}
    FiltersAPI(client).get_filter_results(
        filter_id=7, project_id=3, params=caller_params
    )
    assert caller_params == {"include": "data.itemType"}
    assert client.get_all.call_args.kwargs["params"] == {
        "include": "data.itemType",
        "project": 3,
    }


def test_get_filter_results_without_project_sends_no_project_param():
    client = Mock()
    FiltersAPI(client).get_filter_results(filter_id=7)
    assert "project" not in client.get_all.call_args.kwargs["params"]


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_filter(filter_id=1),
        lambda api: api.get_filter_count(filter_id=1),
    ],
    ids=["filter", "count"],
)
def test_filter_reads_wrap_core_exception(call):
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(FiltersAPI(client))


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_filters_maps_arguments_to_query_parameters():
    client = Mock()
    params = {"author": 1, "a": 1}
    FiltersAPI(client).get_filters(
        params=params,
        project=3,
        author=4,
        filter_scope=["ALL_PROJECTS", "BOUND_PROJECT"],
        access_specifier="PUBLIC",
    )
    assert get_all_params(client) == {
        "project": 3,
        "author": 4,
        "filterScope": ["ALL_PROJECTS", "BOUND_PROJECT"],
        "accessSpecifier": "PUBLIC",
        "a": 1,
    }
    assert params == {"author": 1, "a": 1}


def test_get_filters_sends_no_new_parameters_by_default():
    client = Mock()
    FiltersAPI(client).get_filters(params={"a": 1})
    assert get_all_params(client) == {"a": 1}


def test_get_filter_results_maps_last_activity_date():
    client = Mock()
    params = {"lastActivityDate": ["old"]}
    FiltersAPI(client).get_filter_results(
        filter_id=7, params=params, last_activity_date=["2026-01-01T00:00:00Z"]
    )
    assert get_all_params(client) == {"lastActivityDate": ["2026-01-01T00:00:00Z"]}
    assert params == {"lastActivityDate": ["old"]}
