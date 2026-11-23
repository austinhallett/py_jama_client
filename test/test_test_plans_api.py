import warnings
from unittest.mock import Mock

import pytest

from py_jama_client.apis import test_cycles_api as cycles_module
from py_jama_client.apis import test_plans_api as plans_module
from py_jama_client.client import JamaClient
from py_jama_client.exceptions import (
    APIClientException,
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ID = 2147483647


@pytest.fixture(scope="function")
def test_plans_api(get_test_jama_client):
    return plans_module.TestPlansAPI(get_test_jama_client)


def get_json(client, resource):
    response = client.get(resource)
    JamaClient.handle_response_status(response)
    return response.json()


def test_post_test_plan(test_plans_api, get_test_jama_client, real_project, request):
    name = f"zz-char-{request.node.name}"
    response = test_plans_api.post_test_plan(real_project, {"name": name})
    plan_id = response.meta["id"]
    try:
        assert isinstance(plan_id, int)
        assert response.meta["status"] == "Created"
        plan = get_json(get_test_jama_client, f"testplans/{plan_id}")["data"]
        assert plan["fields"]["name"] == name
        assert plan["project"] == real_project
    finally:
        try:
            test_plans_api.delete_test_plan(plan_id)
        except APIException as err:
            warnings.warn(f"zz-char plan {plan_id} not deleted: {err}")


def test_post_test_group(
    test_plans_api, get_test_jama_client, scratch_test_plan, current_user
):
    response = test_plans_api.post_test_group(
        scratch_test_plan, "zz-char-group", assigned_to=current_user["id"]
    )
    group_id = response.meta["id"]
    assert isinstance(group_id, int)
    assert response.meta["status"] == "Created"
    group = get_json(
        get_test_jama_client, f"testplans/{scratch_test_plan}/testgroups/{group_id}"
    )["data"]
    assert group["name"] == "zz-char-group"
    assert group["assignedTo"] == current_user["id"]


def test_post_test_group_test_case(
    test_plans_api, get_test_jama_client, scratch_test_plan, real_test_case
):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    response = test_plans_api.post_test_group_test_case(
        scratch_test_plan, group_id, real_test_case
    )
    assert response.meta["status"] == "Created"
    cases = get_json(
        get_test_jama_client,
        f"testplans/{scratch_test_plan}/testgroups/{group_id}/testcases",
    )["data"]
    assert real_test_case in {case["id"] for case in cases}


def test_delete_test_plan(test_plans_api, get_test_jama_client, scratch_test_plan):
    assert test_plans_api.delete_test_plan(scratch_test_plan) == 204
    with pytest.raises(ResourceNotFoundException):
        get_json(get_test_jama_client, f"testplans/{scratch_test_plan}")


def test_post_test_plan_missing_project(test_plans_api, request):
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.post_test_plan(
            MISSING_ID, {"name": f"zz-char-{request.node.name}"}
        )


def test_post_test_group_missing_plan(test_plans_api):
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.post_test_group(MISSING_ID, "zz-char-group")


def test_post_test_group_test_case_not_a_test_case(
    test_plans_api, scratch_test_plan, real_abstract_item
):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    with pytest.raises(APIClientException) as excinfo:
        test_plans_api.post_test_group_test_case(
            scratch_test_plan, group_id, real_abstract_item
        )
    assert excinfo.value.status_code == 400
    assert "no test case with the ID" in str(excinfo.value)


def test_delete_test_plan_missing_plan(test_plans_api):
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.delete_test_plan(MISSING_ID)


def group_id_named(test_plans_api, plan_id, name):
    groups = test_plans_api.get_test_groups(plan_id).data
    group_id = next((group["id"] for group in groups if group["name"] == name), None)
    if group_id is None:
        pytest.fail(f"no group {name!r} in plan {plan_id}")
    return group_id


def test_get_test_plans(test_plans_api, real_project, real_test_plan, bounded_pages):
    response = test_plans_api.get_test_plans(params={"project": real_project})
    total_results = bounded_pages["offset_total"]
    assert total_results <= 12
    assert len(response.data) == total_results
    assert all({"id", "fields", "project", "itemType"} <= set(p) for p in response.data)
    assert {p["project"] for p in response.data} == {real_project}
    assert real_test_plan in {p["id"] for p in response.data}


def test_get_test_plan(test_plans_api, real_project, real_test_plan):
    response = test_plans_api.get_test_plan(real_test_plan)
    assert response.data["id"] == real_test_plan
    assert response.data["project"] == real_project
    assert response.data["fields"]["name"] == "Widget Verification Plan"
    assert response.data["documentKey"] == response.data["fields"]["documentKey"]
    assert response.meta["status"] == "OK"


def test_get_test_plan_activities(test_plans_api, real_test_plan):
    response = test_plans_api.get_test_plan_activities(real_test_plan)
    assert len(response.data) > 0
    for activity in response.data:
        assert {"id", "item", "date", "user", "action", "eventType"} <= set(activity)
    assert real_test_plan in {activity["item"] for activity in response.data}
    assert "CREATE" in {activity["eventType"] for activity in response.data}


@pytest.mark.parametrize(
    "method",
    [
        "get_test_plan_attachments",
        "get_test_plan_comments",
        "get_test_plan_downstream_related",
        "get_test_plan_downstream_relationships",
        "get_test_plan_upstream_related",
        "get_test_plan_upstream_relationships",
        "get_test_plan_links",
        "get_test_plan_tags",
    ],
)
def test_get_test_plan_collections_empty_on_fixture_plan(
    test_plans_api, real_test_plan, method
):
    response = getattr(test_plans_api, method)(real_test_plan)
    assert response.data == []
    assert response.meta["pageInfo"]["totalResults"] == 0


def test_get_test_plan_lock(test_plans_api, real_test_plan):
    response = test_plans_api.get_test_plan_lock(real_test_plan)
    assert response.data["locked"] is False


def test_get_test_plan_test_cycles(test_plans_api, real_test_plan):
    response = test_plans_api.get_test_plan_test_cycles(real_test_plan)
    assert "Cycle 1" in {cycle["fields"]["name"] for cycle in response.data}
    for cycle in response.data:
        assert {"id", "fields", "project"} <= set(cycle)
        assert cycle["fields"]["testPlan"] == real_test_plan


def test_get_test_groups(test_plans_api, real_test_plan):
    response = test_plans_api.get_test_groups(real_test_plan)
    names = {group["name"] for group in response.data}
    assert {"Mounting Tests", "Regulatory Tests"} <= names
    assert all({"id", "name"} <= set(group) for group in response.data)


def test_get_test_group(test_plans_api, real_test_plan):
    group_id = group_id_named(test_plans_api, real_test_plan, "Regulatory Tests")
    response = test_plans_api.get_test_group(real_test_plan, group_id)
    assert response.data["id"] == group_id
    assert response.data["name"] == "Regulatory Tests"


def test_get_test_group_test_cases(test_plans_api, real_test_plan, real_test_case):
    group_id = group_id_named(test_plans_api, real_test_plan, "Mounting Tests")
    response = test_plans_api.get_test_group_test_cases(real_test_plan, group_id)
    assert real_test_case in {case["id"] for case in response.data}
    for case in response.data:
        assert {"id", "documentKey", "fields", "project"} <= set(case)


def test_get_test_group_test_case(test_plans_api, real_test_plan, real_test_case):
    group_id = group_id_named(test_plans_api, real_test_plan, "Mounting Tests")
    response = test_plans_api.get_test_group_test_case(
        real_test_plan, group_id, real_test_case
    )
    assert response.data["id"] == real_test_case
    assert "name" in response.data["fields"]


def test_get_test_plan_versions(test_plans_api, real_test_plan):
    response = test_plans_api.get_test_plan_versions(real_test_plan)
    assert len(response.data) > 0
    for version in response.data:
        assert {"item", "versionNumber", "versionedItem", "createdDate"} <= set(version)
        assert version["item"] == real_test_plan
        assert version["versionedItem"] == [real_test_plan, version["versionNumber"]]
    assert 1 in {version["versionNumber"] for version in response.data}


def test_get_test_plan_version(test_plans_api, real_test_plan):
    response = test_plans_api.get_test_plan_version(real_test_plan, 1)
    assert response.data["item"] == real_test_plan
    assert response.data["versionNumber"] == 1
    assert response.data["changeDetails"] == "Initial Creation"


def test_get_test_plan_versioned_item(test_plans_api, real_project, real_test_plan):
    response = test_plans_api.get_test_plan_versioned_item(real_test_plan, 1)
    assert response.data["id"] == real_test_plan
    assert response.data["project"] == real_project
    assert response.data["fields"]["name"] == "Widget Verification Plan"


def test_get_test_plan_unknown_plan(test_plans_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.get_test_plan(MISSING_ID)
    assert excinfo.value.status_code == 404
    assert excinfo.value.reason
    assert "does not exist" in excinfo.value.reason


def test_get_test_groups_unknown_plan(test_plans_api):
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.get_test_groups(MISSING_ID)


def test_get_test_plan_tags_unknown_plan(test_plans_api):
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.get_test_plan_tags(MISSING_ID)


def test_get_test_group_unknown_group_on_real_plan(test_plans_api, real_test_plan):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.get_test_group(real_test_plan, MISSING_ID)
    assert excinfo.value.reason
    assert "test group" in excinfo.value.reason


def test_get_test_group_test_case_unknown_test_case(test_plans_api, real_test_plan):
    group_id = group_id_named(test_plans_api, real_test_plan, "Mounting Tests")
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.get_test_group_test_case(real_test_plan, group_id, MISSING_ID)


def test_get_test_plan_tag_real_tag_not_on_plan(
    test_plans_api, real_test_plan, real_tag
):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.get_test_plan_tag(real_test_plan, real_tag)
    assert excinfo.value.reason
    assert "not found on item" in excinfo.value.reason


def test_get_test_plan_link_unknown_link(test_plans_api, real_test_plan):
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.get_test_plan_link(real_test_plan, MISSING_ID)


def test_get_test_plan_version_unknown_version(test_plans_api, real_test_plan):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.get_test_plan_version(real_test_plan, 9999)
    assert excinfo.value.reason
    assert "version was not found" in excinfo.value.reason


def test_patch_test_plan(test_plans_api, scratch_test_plan):
    patches = [{"op": "replace", "path": "/fields/name", "value": "zz-char-patched"}]
    assert test_plans_api.patch_test_plan(scratch_test_plan, patches) == 200
    plan = test_plans_api.get_test_plan(scratch_test_plan).data
    assert plan["fields"]["name"] == "zz-char-patched"


def test_put_test_plan(test_plans_api, scratch_test_plan):
    assert (
        test_plans_api.put_test_plan(scratch_test_plan, {"name": "zz-char-put"}) == 200
    )
    plan = test_plans_api.get_test_plan(scratch_test_plan).data
    assert plan["fields"]["name"] == "zz-char-put"
    versions = test_plans_api.get_test_plan_versions(scratch_test_plan).data
    assert len(versions) == 2
    assert (
        "zz-char-put"
        in max(versions, key=lambda v: v["versionNumber"])["changeDetails"]
    )


def test_put_test_plan_archived(test_plans_api, scratch_test_plan):
    assert test_plans_api.put_test_plan_archived(scratch_test_plan, True) == 200
    assert test_plans_api.get_test_plan(scratch_test_plan).data["archived"] is True
    assert test_plans_api.put_test_plan_archived(scratch_test_plan, False) == 200
    assert test_plans_api.get_test_plan(scratch_test_plan).data["archived"] is False


def test_test_plan_tag_round_trip(test_plans_api, scratch_test_plan, real_tag):
    response = test_plans_api.post_test_plan_tag(scratch_test_plan, real_tag)
    assert response.meta["status"] == "Created"
    assert response.meta["id"] == real_tag
    tags = test_plans_api.get_test_plan_tags(scratch_test_plan).data
    assert [tag["id"] for tag in tags] == [real_tag]
    tag = test_plans_api.get_test_plan_tag(scratch_test_plan, real_tag).data
    assert tag["id"] == real_tag
    assert {"name", "project"} <= set(tag)
    assert test_plans_api.delete_test_plan_tag(scratch_test_plan, real_tag) == 204
    assert test_plans_api.get_test_plan_tags(scratch_test_plan).data == []


def test_post_test_plan_tag_twice(test_plans_api, scratch_test_plan, real_tag):
    test_plans_api.post_test_plan_tag(scratch_test_plan, real_tag)
    with pytest.raises(APIClientException) as excinfo:
        test_plans_api.post_test_plan_tag(scratch_test_plan, real_tag)
    assert excinfo.value.status_code == 400
    assert "already has the tag" in str(excinfo.value)


def test_delete_test_plan_tag_not_on_plan(test_plans_api, scratch_test_plan, real_tag):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.delete_test_plan_tag(scratch_test_plan, real_tag)
    assert excinfo.value.reason
    assert "was not found on item" in excinfo.value.reason


def test_test_plan_link_round_trip(test_plans_api, scratch_test_plan):
    url = "https://jama.example.com/widget-spec"
    response = test_plans_api.post_test_plan_link(scratch_test_plan, url, "Widget spec")
    assert response.meta["status"] == "Created"
    link_id = response.meta["id"]
    link = test_plans_api.get_test_plan_link(scratch_test_plan, link_id).data
    assert link == {"id": link_id, "url": url, "description": "Widget spec"}
    links = test_plans_api.get_test_plan_links(scratch_test_plan).data
    assert [item["id"] for item in links] == [link_id]
    new_url = "https://jama.example.com/widget-spec-v2"
    assert (
        test_plans_api.put_test_plan_link(
            scratch_test_plan, link_id, new_url, "Widget spec v2"
        )
        == 200
    )
    link = test_plans_api.get_test_plan_link(scratch_test_plan, link_id).data
    assert link == {"id": link_id, "url": new_url, "description": "Widget spec v2"}
    assert test_plans_api.delete_test_plan_link(scratch_test_plan, link_id) == 204
    assert test_plans_api.get_test_plan_links(scratch_test_plan).data == []


def test_delete_test_plan_link_deleted_link(test_plans_api, scratch_test_plan):
    link_id = test_plans_api.post_test_plan_link(
        scratch_test_plan, "https://jama.example.com/widget-spec", "Widget spec"
    ).meta["id"]
    test_plans_api.delete_test_plan_link(scratch_test_plan, link_id)
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.delete_test_plan_link(scratch_test_plan, link_id)
    assert excinfo.value.reason
    assert "does not exist" in excinfo.value.reason


def test_put_test_plan_lock(test_plans_api, scratch_test_plan, current_user):
    assert test_plans_api.put_test_plan_lock(scratch_test_plan, True) == 200
    lock = test_plans_api.get_test_plan_lock(scratch_test_plan).data
    assert lock["locked"] is True
    assert lock["lockedBy"] == current_user["id"]
    assert "lastLockedDate" in lock
    assert test_plans_api.put_test_plan_lock(scratch_test_plan, False) == 200
    lock = test_plans_api.get_test_plan_lock(scratch_test_plan).data
    assert lock["locked"] is False
    assert "lockedBy" not in lock


def test_put_test_group(test_plans_api, scratch_test_plan, current_user):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    assert (
        test_plans_api.put_test_group(
            scratch_test_plan,
            group_id,
            "zz-char-renamed",
            assigned_to=current_user["id"],
        )
        == 200
    )
    group = test_plans_api.get_test_group(scratch_test_plan, group_id).data
    assert group["name"] == "zz-char-renamed"
    assert group["assignedTo"] == current_user["id"]
    assert (
        test_plans_api.put_test_group(scratch_test_plan, group_id, "zz-char-g3") == 200
    )
    group = test_plans_api.get_test_group(scratch_test_plan, group_id).data
    assert group["name"] == "zz-char-g3"
    assert "assignedTo" not in group


def test_delete_test_group(test_plans_api, scratch_test_plan):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    assert test_plans_api.delete_test_group(scratch_test_plan, group_id) == 204
    assert group_id not in {
        group["id"] for group in test_plans_api.get_test_groups(scratch_test_plan).data
    }
    with pytest.raises(ResourceNotFoundException):
        test_plans_api.get_test_group(scratch_test_plan, group_id)


def test_delete_test_group_deleted_group(test_plans_api, scratch_test_plan):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    test_plans_api.delete_test_group(scratch_test_plan, group_id)
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.delete_test_group(scratch_test_plan, group_id)
    assert excinfo.value.reason
    assert "does not exist" in excinfo.value.reason


def test_delete_test_group_test_case(test_plans_api, scratch_test_plan, real_test_case):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    test_plans_api.post_test_group_test_case(
        scratch_test_plan, group_id, real_test_case
    )
    assert (
        test_plans_api.delete_test_group_test_case(
            scratch_test_plan, group_id, real_test_case
        )
        == 204
    )
    cases = test_plans_api.get_test_group_test_cases(scratch_test_plan, group_id).data
    assert cases == []


def test_delete_test_group_test_case_not_in_group(
    test_plans_api, scratch_test_plan, real_test_case
):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.delete_test_group_test_case(
            scratch_test_plan, group_id, real_test_case
        )
    assert excinfo.value.reason
    assert "was not found in the test group" in excinfo.value.reason


def test_post_testplans_testcycles(
    test_plans_api, get_test_jama_client, scratch_test_plan, real_test_case
):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    test_plans_api.post_test_group_test_case(
        scratch_test_plan, group_id, real_test_case
    )
    response = test_plans_api.post_testplans_testcycles(
        scratch_test_plan,
        "zz-char-cycle",
        "2026-01-05",
        "2026-01-30",
        testgroups_to_include=[group_id],
    )
    assert response.meta["status"] == "Created"
    cycle_id = response.meta["id"]
    cycles = test_plans_api.get_test_plan_test_cycles(scratch_test_plan).data
    assert [cycle["id"] for cycle in cycles] == [cycle_id]
    fields = cycles[0]["fields"]
    assert fields["name"] == "zz-char-cycle"
    assert fields["testPlan"] == scratch_test_plan
    assert (fields["startDate"], fields["endDate"]) == ("2026-01-05", "2026-01-30")
    cycles_api = cycles_module.TestCyclesAPI(get_test_jama_client)
    runs = cycles_api.get_test_cycle_runs(cycle_id).data
    assert len(runs) == 1
    assert runs[0]["fields"]["testCase"] == real_test_case
    assert test_plans_api.delete_test_plan(scratch_test_plan) == 204
    with pytest.raises(ResourceNotFoundException):
        cycles_api.get_test_cycle(cycle_id)
    with pytest.raises(ResourceNotFoundException):
        cycles_api.get_test_cycle_runs(cycle_id)


def test_post_testplans_testcycles_no_test_runs_to_copy(
    test_plans_api, scratch_test_plan
):
    with pytest.raises(APIClientException) as excinfo:
        test_plans_api.post_testplans_testcycles(
            scratch_test_plan, "zz-char-cycle", "2026-01-05", "2026-01-30"
        )
    assert excinfo.value.status_code == 400
    assert "no previous test runs" in str(excinfo.value)


def test_post_test_plan_attachment_missing_attachment(
    test_plans_api, scratch_test_plan
):
    with pytest.raises(APIClientException) as excinfo:
        test_plans_api.post_test_plan_attachment(scratch_test_plan, MISSING_ID)
    assert excinfo.value.status_code == 400
    assert "does not exist" in str(excinfo.value)


def test_delete_test_plan_attachment_not_on_plan(test_plans_api, scratch_test_plan):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_plans_api.delete_test_plan_attachment(scratch_test_plan, MISSING_ID)
    assert excinfo.value.reason
    assert "is not associated with item" in excinfo.value.reason


def test_test_plan_attachment_link_round_trip(
    test_plans_api, scratch_test_plan, real_scratch_attachment
):
    linked = False
    try:
        response = test_plans_api.post_test_plan_attachment(
            scratch_test_plan, real_scratch_attachment
        )
        linked = True
        assert response.meta["status"] == "Created"
        attached = test_plans_api.get_test_plan_attachments(scratch_test_plan).data
        assert [a["id"] for a in attached] == [real_scratch_attachment]
        status = test_plans_api.delete_test_plan_attachment(
            scratch_test_plan, real_scratch_attachment
        )
        linked = status != 204
        assert status == 204
        assert test_plans_api.get_test_plan_attachments(scratch_test_plan).data == []
    finally:
        if linked:
            try:
                test_plans_api.delete_test_plan_attachment(
                    scratch_test_plan, real_scratch_attachment
                )
            except Exception as error:  # noqa: BLE001
                warnings.warn(f"could not unlink the scratch attachment: {error}")


def offline_api(status_code=201, json_body=None):
    client = Mock()
    client.post.return_value = Mock(
        status_code=status_code,
        json=Mock(return_value=json_body or {"meta": {"id": 7}}),
        text="",
    )
    client.delete.return_value = Mock(status_code=204)
    return plans_module.TestPlansAPI(client), client


def test_post_test_plan_params_untouched():
    api, _client = offline_api()
    params = {"setGlobalIdManually": False}
    fields = {"name": "plan"}
    response = api.post_test_plan(5, fields, params=params)
    assert params == {"setGlobalIdManually": False}
    assert fields == {"name": "plan"}
    assert response.meta["id"] == 7


def test_post_test_group_omits_unassigned():
    api, client = offline_api()
    api.post_test_group(5, "group")
    assert "assignedTo" not in client.post.call_args.kwargs["json"]
    api.post_test_group(5, "group", assigned_to=3)
    assert client.post.call_args.kwargs["json"]["assignedTo"] == 3


def test_delete_test_plan_returns_status_code():
    api, _client = offline_api()
    assert api.delete_test_plan(5) == 204


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_test_plan(5, {"name": "plan"}),
        lambda api: api.post_test_group(5, "group"),
        lambda api: api.post_test_group_test_case(5, 6, 7),
    ],
    ids=["plan", "group", "group_test_case"],
)
def test_post_wraps_core_exception(call):
    api, client = offline_api()
    client.post.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_delete_test_plan_wraps_core_exception():
    api, client = offline_api()
    client.delete.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        api.delete_test_plan(5)


def test_get_test_plan_passes_params_and_kwargs():
    client = Mock()
    client.get.return_value = Mock(
        status_code=200, json=Mock(return_value={"data": {"id": 5}})
    )
    params = {"include": "data.project"}
    plans_module.TestPlansAPI(client).get_test_plan(5, params=params, timeout=3)
    client.get.assert_called_once_with("testplans/5", params, timeout=3)
    assert params == {"include": "data.project"}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_test_plan(5),
        lambda api: api.patch_test_plan(5, []),
        lambda api: api.put_test_plan(5, {}),
        lambda api: api.put_test_plan_archived(5, True),
        lambda api: api.delete_test_plan_tag(5, 6),
        lambda api: api.put_test_plan_lock(5, True),
    ],
    ids=["get", "patch", "put", "archived", "delete_tag", "lock"],
)
def test_test_plan_calls_wrap_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "patch", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_post_testplans_testcycles_sends_run_generation_config():
    api, client = offline_api()
    api.post_testplans_testcycles(
        5, "cycle", "2026-01-05", "2026-01-30", [3], ["PASSED"]
    )
    body = client.post.call_args.kwargs["json"]
    assert body["testRunGenerationConfig"] == {
        "testGroupsToInclude": [3],
        "testRunStatusesToInclude": ["PASSED"],
    }


def test_post_testplans_testcycles_wraps_core_exception():
    api, client = offline_api()
    client.post.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        api.post_testplans_testcycles(5, "cycle", "2026-01-05", "2026-01-30")


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_test_plans_maps_project():
    client = Mock()
    params = {"project": 1}
    plans_module.TestPlansAPI(client).get_test_plans(params=params, project=3)
    assert get_all_params(client) == {"project": 3}
    assert params == {"project": 1}
    plans_module.TestPlansAPI(client).get_test_plans()
    assert get_all_params(client) is None


def test_get_test_plan_comments_maps_root_comments_only():
    client = Mock()
    params = {"rootCommentsOnly": False}
    plans_module.TestPlansAPI(client).get_test_plan_comments(
        5, params=params, root_comments_only=True
    )
    assert get_all_params(client) == {"rootCommentsOnly": True}
    assert params == {"rootCommentsOnly": False}
    plans_module.TestPlansAPI(client).get_test_plan_comments(5)
    assert get_all_params(client) is None


def test_post_test_plan_maps_parent_test_plan_folder_id():
    api, client = offline_api()
    api.post_test_plan(5, {"name": "plan"}, parent_test_plan_folder_id=9)
    assert client.post.call_args.kwargs["json"] == {
        "fields": {"name": "plan"},
        "project": 5,
        "parentTestPlanFolderId": 9,
    }
    api.post_test_plan(5, {"name": "plan"})
    assert "parentTestPlanFolderId" not in client.post.call_args.kwargs["json"]


def test_put_test_plan_maps_location():
    api, client = offline_api()
    client.put.return_value = Mock(status_code=200)
    location = {"parent": {"item": 9}, "sortOrder": 1}
    api.put_test_plan(5, {"name": "plan"}, location=location)
    assert client.put.call_args.kwargs["json"] == {
        "fields": {"name": "plan"},
        "location": location,
    }
    api.put_test_plan(5, {"name": "plan"})
    assert client.put.call_args.kwargs["json"] == {"fields": {"name": "plan"}}
