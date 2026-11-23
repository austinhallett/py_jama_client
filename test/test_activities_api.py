from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from py_jama_client.apis.activities_api import ActivitiesAPI
from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
    UnauthorizedException,
)

MISSING_ACTIVITY_ID = 2147483647
SINCE = "2026-11-18T20:58:00Z"
UNTIL = "2026-11-18T20:59:00Z"


@pytest.fixture(scope="function")
def activities_api(get_test_jama_client, bounded_pages):
    return ActivitiesAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def created_item_activity(activities_api, real_project, real_abstract_item):
    created = (
        ItemsAPI(activities_api.client).get_item(real_abstract_item).data["createdDate"]
    )
    moment = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%f%z")
    window = [
        (moment + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for offset in (-1, 1)
    ]
    response = activities_api.get_activities(
        real_project, event_type=["CREATE"], object_type=["ITEM"], date=window
    )
    for activity in response.data:
        if activity["item"] == real_abstract_item:
            return activity
    pytest.fail("The create activity of the fixture item was not found.")


def unfiltered_total(activities_api, real_project, bounded_pages):
    activities_api.get_activities(real_project)
    return bounded_pages["offset_total"]


def test_get_activities(activities_api, real_project, bounded_pages):
    response = activities_api.get_activities(real_project)
    assert response.data
    assert len(response.data) == min(bounded_pages["offset_total"], 12)
    assert all(
        {"id", "date", "eventType", "objectType", "user"} <= set(a)
        for a in response.data
    )


def test_get_activities_filters_by_event_type(
    activities_api, real_project, bounded_pages
):
    total = unfiltered_total(activities_api, real_project, bounded_pages)
    response = activities_api.get_activities(real_project, event_type=["CREATE"])
    assert response.data
    assert {a["eventType"] for a in response.data} == {"CREATE"}
    assert bounded_pages["offset_total"] < total


def test_get_activities_filters_by_object_type(
    activities_api, real_project, bounded_pages
):
    total = unfiltered_total(activities_api, real_project, bounded_pages)
    response = activities_api.get_activities(real_project, object_type=["ITEM"])
    assert response.data
    assert {a["objectType"] for a in response.data} == {"ITEM"}
    assert bounded_pages["offset_total"] < total


def test_get_activities_filters_by_item_type(
    activities_api, real_project, real_item_type, bounded_pages
):
    total = unfiltered_total(activities_api, real_project, bounded_pages)
    response = activities_api.get_activities(real_project, item_type=[real_item_type])
    assert response.data
    assert {a["itemType"] for a in response.data} == {real_item_type}
    assert bounded_pages["offset_total"] < total


def test_get_activities_filters_by_date_range(
    activities_api, real_project, bounded_pages
):
    total = unfiltered_total(activities_api, real_project, bounded_pages)
    response = activities_api.get_activities(real_project, date=[SINCE, UNTIL])
    assert response.data
    assert all(SINCE[:19] <= a["date"][:19] <= UNTIL[:19] for a in response.data)
    assert bounded_pages["offset_total"] < total


def test_get_activity(activities_api, created_item_activity, real_abstract_item):
    response = activities_api.get_activity(created_item_activity["id"])
    assert response.data["id"] == created_item_activity["id"]
    assert response.data["item"] == created_item_activity["item"]
    assert response.data["item"] == real_abstract_item
    assert response.data["eventType"] == "CREATE"
    assert response.data["objectType"] == "ITEM"


def test_get_activity_missing_activity(activities_api):
    with pytest.raises(ResourceNotFoundException):
        activities_api.get_activity(MISSING_ACTIVITY_ID)


def test_get_activity_affected_items(activities_api, created_item_activity):
    response = activities_api.get_activity_affected_items(
        created_item_activity["id"], allowed_results_per_page=5
    )
    assert created_item_activity["item"] in {item["id"] for item in response.data}
    assert all({"id", "project", "itemType"} <= set(item) for item in response.data)


def test_get_activity_affected_items_missing_activity(activities_api):
    with pytest.raises(ResourceNotFoundException):
        activities_api.get_activity_affected_items(
            MISSING_ACTIVITY_ID, allowed_results_per_page=5
        )


def test_restore_activity_items(activities_api, real_project, scratch_item):
    items_api = ItemsAPI(activities_api.client)
    item_id = scratch_item.create()
    created = items_api.get_item(item_id).data["createdDate"]
    moment = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%f%z")
    window = [
        (moment + offset).strftime("%Y-%m-%dT%H:%M:%SZ")
        for offset in (timedelta(seconds=-1), timedelta(hours=1))
    ]
    items_api.delete_item(item_id)
    deletes = activities_api.get_activities(
        real_project, event_type=["DELETE"], object_type=["ITEM"], date=window
    ).data
    delete = next((a for a in deletes if a.get("item") == item_id), None)
    assert delete is not None
    response = activities_api.restore_activity_items(delete["id"])
    assert response.meta["status"] == "OK"
    assert items_api.get_item(item_id).data["id"] == item_id


def test_get_admin_activities(activities_api, real_project, bounded_pages):
    response = activities_api.get_admin_activities(project_id=real_project)
    assert response.data
    assert len(response.data) <= 12
    assert all(
        {"id", "date", "user", "action", "details"} <= set(a) for a in response.data
    )


def test_get_admin_activities_filter_term(activities_api, real_project):
    # Quoted text matches as a phrase; unquoted words match any of them.
    phrase = activities_api.get_admin_activities(
        filter_term='"Tag added"', project_id=real_project
    ).data
    words = activities_api.get_admin_activities(
        filter_term="Tag added", project_id=real_project
    ).data
    assert phrase
    assert {a["action"] for a in phrase} == {"Tag added"}
    assert {a["id"] for a in phrase} < {a["id"] for a in words}


def test_get_admin_activities_by_object_without_permission(
    activities_api, real_project
):
    with pytest.raises(UnauthorizedException):
        activities_api.get_admin_activities(object_type=1, object_id=real_project)


def test_get_admin_activities_docs(activities_api):
    response = activities_api.get_admin_activities(filter_term="example", project_id=1)
    assert [a["objectType"] for a in response.data] == ["PROJECT", "PROJECT"]
    assert response.data[0]["eventType"] == "CREATE"


def offline_api():
    client = Mock()
    client.get.return_value = Mock(
        status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
    )
    client.post.return_value = client.get.return_value
    return ActivitiesAPI(client), client


def test_get_activities_maps_each_filter_to_its_query_parameter():
    api, client = offline_api()
    api.get_activities(
        7,
        event_type=["CREATE"],
        object_type=["ITEM"],
        item_type=[24],
        date=[SINCE],
        delete_events=True,
    )
    assert client.get_all.call_args.args[:2] == (
        "activities",
        {
            "project": 7,
            "eventType": ["CREATE"],
            "objectType": ["ITEM"],
            "itemType": [24],
            "date": [SINCE],
            "deleteEvents": True,
        },
    )


def test_get_activities_sends_only_the_project_by_default():
    api, client = offline_api()
    api.get_activities(7)
    assert client.get_all.call_args.args[1] == {"project": 7}


def test_get_activities_merges_project_into_a_copy_of_caller_params():
    api, client = offline_api()
    params = {"a": 1}
    api.get_activities(7, event_type=["CREATE"], params=params)
    assert client.get_all.call_args.args[1] == {
        "a": 1,
        "project": 7,
        "eventType": ["CREATE"],
    }
    assert params == {"a": 1}


def test_get_admin_activities_maps_filters_to_query_parameters():
    api, client = offline_api()
    api.get_admin_activities(filter_term="x", project_id=7)
    assert client.get_all.call_args.args[:2] == (
        "activities/adminActivity",
        {"filterTerm": "x", "projectId": 7},
    )


def test_get_admin_activities_sends_no_filters_by_default():
    api, client = offline_api()
    api.get_admin_activities()
    assert client.get_all.call_args.args[1] == {}


def test_get_admin_activities_maps_object_filters_to_query_parameters():
    api, client = offline_api()
    api.get_admin_activities(filter_term="x", object_type=1, object_id=9)
    assert client.get_all.call_args.args[:2] == (
        "activities/adminActivity",
        {"filterTerm": "x", "objectType": 1, "objectId": 9},
    )


@pytest.mark.parametrize(
    "filters",
    [{"object_type": 1}, {"object_id": 9}],
    ids=["type_only", "id_only"],
)
def test_get_admin_activities_object_filters_go_together(filters):
    api, client = offline_api()
    with pytest.raises(ValueError, match="together"):
        api.get_admin_activities(**filters)
    client.get_all.assert_not_called()


def test_get_admin_activities_object_filters_exclude_project():
    api, client = offline_api()
    with pytest.raises(ValueError, match="project_id"):
        api.get_admin_activities(project_id=7, object_type=1, object_id=9)
    client.get_all.assert_not_called()


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_activity(1),
        lambda api: api.restore_activity_items(1),
    ],
    ids=["get_activity", "restore"],
)
def test_activity_calls_wrap_core_exception(call):
    api, client = offline_api()
    client.get.side_effect = CoreException("boom")
    client.post.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)
