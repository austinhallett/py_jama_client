import logging
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from unittest.mock import Mock

import pytest

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.constants import DEFAULT_RETRY_AFTER_SECONDS, MAX_THROTTLE_WAITS
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
    TooManyRequestsException,
    UnauthorizedException,
)
from py_jama_client.response import ClientResponse


@pytest.fixture(scope="function")
def relationships_api(get_test_jama_client, bounded_pages):
    api_instance = RelationshipsAPI(get_test_jama_client)
    return api_instance


def test_get_relationships(relationships_api, real_project, bounded_pages):
    response = relationships_api.get_relationships(project_id=real_project)
    total_results = (
        bounded_pages["last_id_total"]
        if bounded_pages["last_id"]
        else bounded_pages["offset_total"]
    )
    assert total_results >= 12
    assert len(response.data) == 12
    page_sizes = bounded_pages["last_id"] or bounded_pages["offset"]
    assert page_sizes == [5, 5, 2]


def test_get_all_lastid(relationships_api, real_project, bounded_pages):
    resource_path = "relationships"
    params = {"project": real_project, "maxResults": 1}
    response = relationships_api.client.get(resource_path, params=params)
    if (
        response.status_code == 400
        and "lastId parameter is now required" in response.text
    ):
        response = relationships_api.get_all_lastid(
            resource_path=resource_path,
            params={"project": real_project},
            allowed_results_per_page=5,
        )
    else:
        pytest.skip("lastId parameter is not required by test Jama instance.")
    total_results = bounded_pages["last_id_total"]
    assert total_results >= 12
    assert len(response.data) == 12
    assert bounded_pages["last_id"] == [5, 5, 2]


def test_get_all_lastid_ignores_zero_total_results_when_page_has_data():
    api = RelationshipsAPI(Mock())
    api.get_page_lastid = Mock(
        side_effect=[
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
        ]
    )

    response = api.get_all_lastid(
        "relationships",
        params={"project": 1, "omitCount": "true"},
        allowed_results_per_page=2,
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert response.meta["pageInfo"]["totalResults"] == 3
    assert [call.args[1] for call in api.get_page_lastid.call_args_list] == [0, 2]


def test_get_all_lastid_merges_linked_data_across_pages():
    api = RelationshipsAPI(Mock())
    api.get_page_lastid = Mock(
        side_effect=[
            ClientResponse(
                {},
                {},
                {"items": {1: {"id": 1, "name": "first"}, 2: {"id": 2}}},
                [{"id": 1}, {"id": 2}],
            ),
            ClientResponse(
                {},
                {},
                {"items": {1: {"id": 1, "name": "updated"}, 3: {"id": 3}}},
                [{"id": 3}],
            ),
        ]
    )

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
    response.json.return_value = {"meta": {}, "links": {}, "linked": {}, "data": []}
    api.client.get = Mock(return_value=response)
    params = {"project": 1}

    api.get_page_lastid("relationships", 10, params=params, allowed_results_per_page=5)

    assert params == {"project": 1}
    assert api.client.get.call_args.kwargs["params"] == {
        "project": 1,
        "lastId": 10,
        "maxResults": 5,
    }


def test_get_all_lastid_honors_retry_after(monkeypatch, caplog):
    api = RelationshipsAPI(Mock())
    # Kept above the default so a fallback to it cannot pass the test
    expected_wait = DEFAULT_RETRY_AFTER_SECONDS + 60
    retry_at = datetime.now(UTC) + timedelta(seconds=expected_wait)
    throttled = TooManyRequestsException(
        "throttled", headers={"Retry-After": format_datetime(retry_at, usegmt=True)}
    )
    api.get_page_lastid = Mock(
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
    response = api.get_all_lastid(
        "relationships", params={"project": 1}, allowed_results_per_page=2
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.args[1] for call in api.get_page_lastid.call_args_list] == [0, 2, 2]
    sleep.assert_called_once()
    assert expected_wait - 10 < sleep.call_args.args[0] <= expected_wait
    assert "Throttled" in caplog.text


def test_get_all_lastid_stops_after_max_consecutive_throttles(monkeypatch):
    api = RelationshipsAPI(Mock())
    api.get_page_lastid = Mock(
        side_effect=[
            TooManyRequestsException("throttled") for _ in range(MAX_THROTTLE_WAITS + 1)
        ]
    )
    sleep = Mock()
    monkeypatch.setattr("time.sleep", sleep)

    with pytest.raises(TooManyRequestsException):
        api.get_all_lastid("relationships", allowed_results_per_page=2)

    assert api.get_page_lastid.call_count == MAX_THROTTLE_WAITS + 1
    assert sleep.call_count == MAX_THROTTLE_WAITS


def test_get_page_lastid(relationships_api, real_project):
    resource_path = "relationships"
    params = {"project": real_project, "maxResults": 1}
    response = relationships_api.client.get(resource_path, params=params)
    if (
        response.status_code == 400
        and "lastId parameter is now required" in response.text
    ):
        response = relationships_api.get_page_lastid(
            resource_path=resource_path, last_id=0, params={"project": real_project}
        )
    else:
        pytest.skip("lastId parameter is not required by test Jama instance.")
    assert response.data != []


def test_get_relationship(relationships_api, real_relationship):
    response = relationships_api.get_relationship(relationship_id=real_relationship)
    assert response.data != []


def test_get_relationship_types(relationships_api):
    response = relationships_api.get_relationship_types()
    assert response.data != []


def test_get_relationship_type(relationships_api, real_relationship_type):
    response = relationships_api.get_relationship_type(
        relationship_type_id=real_relationship_type
    )
    assert response.data != []


def test_get_relationship_types_passes_params():
    client = Mock()
    RelationshipsAPI(client).get_relationship_types(params={"maxResults": 3})
    assert client.get_all.call_args.args[1] == {"maxResults": 3}


def test_get_relationship_types_without_params_sends_none():
    client = Mock()
    RelationshipsAPI(client).get_relationship_types()
    assert client.get_all.call_args.args[1] is None


MISSING_ID = 2147483647
# MOCK's TC (Test Case) item type id, which MOCK's relationship rules let a
# scratch requirement relate to.
RELATABLE_ITEM_TYPE_ID = 26


@pytest.fixture(scope="function")
def scratch_target(
    request, get_test_jama_client, real_project, real_test_case, scratch_item
):
    """Factory for scratch items of a type the project's relationship rules
    let a scratch requirement relate to, created beside the fixture test case;
    deleted with the scratch items."""
    items_api = ItemsAPI(get_test_jama_client)
    parent = items_api.get_item(real_test_case).data["location"]["parent"]["item"]

    def create(suffix="to"):
        item_id = items_api.post_item(
            real_project,
            RELATABLE_ITEM_TYPE_ID,
            RELATABLE_ITEM_TYPE_ID,
            {"item": parent},
            {"name": f"zz-char-{request.node.name}-{suffix}"},
        ).meta["id"]
        scratch_item.track(item_id)
        return item_id

    return create


@pytest.fixture(scope="function")
def scratch_relationship(relationships_api, scratch_item):
    """Factory for relationships between scratch items, deleted on teardown
    (before the items) even if the test failed or already deleted them."""
    created = []

    def create(from_item, to_item, relationship_type=None):
        relationship_id = relationships_api.post_relationship(
            from_item, to_item, relationship_type
        ).meta["id"]
        created.append(relationship_id)
        return relationship_id

    yield create
    failures = []
    for relationship_id in reversed(created):
        try:
            relationships_api.delete_relationship(relationship_id)
        except ResourceNotFoundException:
            pass
        except Exception as error:  # noqa: BLE001
            failures.append((relationship_id, str(error)))
    assert not failures, f"scratch relationships left behind: {failures}"


def test_post_relationship(
    relationships_api, scratch_item, scratch_target, scratch_relationship
):
    source, target = scratch_item.create("from"), scratch_target()
    relationship_id = scratch_relationship(source, target)
    relationship = relationships_api.get_relationship(relationship_id).data
    assert relationship["id"] == relationship_id
    assert (relationship["fromItem"], relationship["toItem"]) == (source, target)
    assert isinstance(relationship["relationshipType"], int)


def test_post_relationship_with_type(
    relationships_api,
    scratch_item,
    scratch_target,
    scratch_relationship,
    real_relationship_type,
):
    source, target = scratch_item.create("from"), scratch_target()
    relationship_id = scratch_relationship(source, target, real_relationship_type)
    relationship = relationships_api.get_relationship(relationship_id).data
    assert relationship["relationshipType"] == real_relationship_type


def test_put_relationship(
    relationships_api,
    scratch_item,
    scratch_target,
    scratch_relationship,
    real_relationship_type,
):
    source, target = scratch_item.create("from"), scratch_target()
    other = scratch_target("other")
    relationship_id = scratch_relationship(source, target)
    relationships_api.put_relationship(
        relationship_id, source, other, real_relationship_type
    )
    relationship = relationships_api.get_relationship(relationship_id).data
    assert (relationship["fromItem"], relationship["toItem"]) == (source, other)
    assert relationship["relationshipType"] == real_relationship_type


def test_delete_relationship(
    relationships_api, scratch_item, scratch_target, scratch_relationship
):
    source, target = scratch_item.create("from"), scratch_target()
    relationship_id = scratch_relationship(source, target)
    assert relationships_api.delete_relationship(relationship_id) == 204
    with pytest.raises(ResourceNotFoundException):
        relationships_api.get_relationship(relationship_id)


def test_delete_relationship_suspect(
    request,
    relationships_api,
    scratch_item,
    scratch_target,
    scratch_relationship,
    get_test_jama_client,
    real_project,
    real_item_type,
    real_abstract_item,
):
    source, target = scratch_item.create("from"), scratch_target()
    relationship_id = scratch_relationship(source, target)
    ItemsAPI(get_test_jama_client).put_item(
        real_project,
        source,
        real_item_type,
        real_item_type,
        {"item": real_abstract_item},
        {
            "name": f"zz-char-{request.node.name}-from",
            "status": scratch_item.status,
            "description": "zz-char-changed upstream",
        },
    )
    assert relationships_api.get_relationship(relationship_id).data["suspect"] is True
    assert relationships_api.delete_relationship_suspect(relationship_id) == 204
    relationship = relationships_api.get_relationship(relationship_id).data
    assert relationship["suspect"] is False


def test_get_relationship_unknown(relationships_api):
    with pytest.raises(ResourceNotFoundException):
        relationships_api.get_relationship(MISSING_ID)


def test_delete_relationship_unknown(relationships_api):
    with pytest.raises(ResourceNotFoundException):
        relationships_api.delete_relationship(MISSING_ID)


def test_get_relationship_rule_sets_docs(relationships_api):
    # The docs show relationship-shaped data for the rule set endpoints.
    response = relationships_api.get_relationship_rule_sets()
    assert len(response.data) == 2
    assert response.meta["pageInfo"]["totalResults"] == 2


def test_get_relationship_rule_set_docs(relationships_api):
    # The docs' example for this endpoint really has an empty data object.
    response = relationships_api.get_relationship_rule_set(9)
    assert response.data == {}
    assert response.meta["status"] == "OK"


def offline_relationships_api(status_code=200, text=""):
    client = Mock()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text=text,
        )
    return RelationshipsAPI(client), client


def test_get_relationships_uses_offset_paging_when_last_id_not_required():
    api, client = offline_relationships_api()
    params = {"include": "x"}
    api.get_relationships(7, params=params, allowed_results_per_page=5)
    probe = client.get.call_args
    assert probe.args == ("relationships",)
    assert probe.kwargs["params"] == {
        "include": "x",
        "project": 7,
        "maxResults": 1,
        "omitCount": "true",
    }
    assert client.get_all.call_args.args == (
        "relationships",
        {"include": "x", "project": 7},
    )
    assert client.get_all.call_args.kwargs["allowed_results_per_page"] == 5
    assert params == {"include": "x"}


def test_get_relationships_other_400_does_not_switch_to_last_id():
    api, client = offline_relationships_api(400, "bad request")
    api.get_all_lastid = Mock()
    api.get_relationships(7)
    api.get_all_lastid.assert_not_called()
    client.get_all.assert_called_once()


@pytest.mark.parametrize("size", [0, 51])
def test_get_all_lastid_rejects_page_size_out_of_range(size):
    api, _ = offline_relationships_api()
    with pytest.raises(ValueError):
        api.get_all_lastid("relationships", allowed_results_per_page=size)


def test_get_all_lastid_stops_after_short_page_without_totals():
    api, _ = offline_relationships_api()
    api.get_page_lastid = Mock(
        side_effect=[
            ClientResponse({}, {}, {}, [{"id": 1}, {"id": 2}]),
            ClientResponse({}, {}, {}, [{"id": 3}]),
        ]
    )
    response = api.get_all_lastid("relationships", allowed_results_per_page=2)
    assert [r["id"] for r in response.data] == [1, 2, 3]
    assert api.get_page_lastid.call_count == 2


def test_get_all_lastid_stops_at_empty_page():
    api, _ = offline_relationships_api()
    api.get_page_lastid = Mock(
        side_effect=[
            ClientResponse({}, {}, {}, [{"id": 1}, {"id": 2}]),
            ClientResponse({}, {}, {}, []),
        ]
    )
    response = api.get_all_lastid("relationships", allowed_results_per_page=2)
    assert [r["id"] for r in response.data] == [1, 2]
    assert api.get_page_lastid.call_args.args[1] == 2


def test_get_page_lastid_without_params_sends_only_paging():
    api, client = offline_relationships_api()
    api.get_page_lastid("relationships", 10, allowed_results_per_page=5)
    assert client.get.call_args.kwargs["params"] == {"lastId": 10, "maxResults": 5}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_page_lastid("relationships", 0),
        lambda api: api.get_relationship(5),
        lambda api: api.post_relationship(1, 2),
        lambda api: api.put_relationship(5, 1, 2),
        lambda api: api.delete_relationship(5),
        lambda api: api.delete_relationship_suspect(5),
        lambda api: api.get_relationship_type(4),
    ],
    ids=[
        "get_page_lastid",
        "get",
        "post",
        "put",
        "delete",
        "delete_suspect",
        "get_type",
    ],
)
def test_relationships_wrap_core_exception(call):
    api, client = offline_relationships_api()
    for verb in ("get", "post", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_relationship_bodies_omit_type_unless_given():
    api, client = offline_relationships_api()
    api.post_relationship(1, 2)
    api.put_relationship(5, 1, 2)
    assert client.post.call_args.kwargs["json"] == {"fromItem": 1, "toItem": 2}
    assert client.put.call_args.kwargs["json"] == {"fromItem": 1, "toItem": 2}
    api.post_relationship(1, 2, 4)
    api.put_relationship(5, 1, 2, 4)
    assert client.post.call_args.kwargs["json"]["relationshipType"] == 4
    assert client.put.call_args.kwargs["json"]["relationshipType"] == 4


def test_get_relationship_rule_sets_without_permission(get_test_jama_client):
    with pytest.raises(UnauthorizedException):
        RelationshipsAPI(get_test_jama_client).get_relationship_rule_sets()


def test_get_relationship_rule_set_without_permission(get_test_jama_client):
    with pytest.raises(UnauthorizedException):
        RelationshipsAPI(get_test_jama_client).get_relationship_rule_set(9)


def test_get_relationship_type_maps_timestamp():
    client = Mock()
    client.get.return_value = Mock(
        status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
    )
    params = {"timestamp": "old"}
    RelationshipsAPI(client).get_relationship_type(
        5, params=params, timestamp="2026-01-01T00:00:00Z"
    )
    assert client.get.call_args.args == (
        "relationshiptypes/5",
        {"timestamp": "2026-01-01T00:00:00Z"},
    )
    assert params == {"timestamp": "old"}
    RelationshipsAPI(client).get_relationship_type(5, params=params)
    assert client.get.call_args.args[1] is params


@pytest.mark.parametrize(
    ("method", "args", "verb"),
    [
        ("get_relationship", (1,), "get"),
        ("get_relationship_types", (), "get_all"),
        ("get_relationship_type", (1,), "get"),
    ],
)
def test_relationship_reads_pass_kwargs_to_the_client(method, args, verb):
    client = Mock()
    getattr(client, verb).return_value.status_code = 200
    getattr(RelationshipsAPI(client), method)(
        *args, timeout=3, headers={"x-custom": "1"}
    )
    kwargs = getattr(client, verb).call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}


def test_get_relationships_forwards_kwargs_to_get_all():
    client = Mock()
    client.get.return_value.status_code = 200
    RelationshipsAPI(client).get_relationships(1, timeout=3)
    assert client.get.call_args.kwargs["timeout"] == 3
    assert client.get_all.call_args.kwargs["timeout"] == 3


def test_get_relationships_forwards_kwargs_to_get_all_lastid():
    client = Mock()
    client.get.return_value = Mock(
        status_code=400, text="lastId parameter is now required"
    )
    api = RelationshipsAPI(client)
    api.get_all_lastid = Mock()
    api.get_relationships(1, timeout=3)
    assert api.get_all_lastid.call_args.kwargs["timeout"] == 3
