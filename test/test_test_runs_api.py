import warnings
from unittest.mock import Mock

import pytest

from py_jama_client.apis import test_cycles_api as cycles_module
from py_jama_client.apis import test_plans_api as plans_module
from py_jama_client.apis import test_runs_api as runs_module
from py_jama_client.exceptions import (
    APIClientException,
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ID = 2147483647


@pytest.fixture(scope="function")
def test_runs_api(get_test_jama_client):
    return runs_module.TestRunsAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def test_plans_api(get_test_jama_client):
    return plans_module.TestPlansAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def scratch_test_run(
    get_test_jama_client, test_plans_api, scratch_test_plan, real_test_case
):
    # Deleting the scratch plan also deletes its cycles and runs.
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    test_plans_api.post_test_group_test_case(
        scratch_test_plan, group_id, real_test_case
    )
    cycle_id = test_plans_api.post_testplans_testcycles(
        scratch_test_plan,
        "zz-char-cycle",
        "2026-01-05",
        "2026-01-30",
        testgroups_to_include=[group_id],
    ).meta["id"]
    cycles_api = cycles_module.TestCyclesAPI(get_test_jama_client)
    run_id = cycles_api.get_test_cycle_runs(cycle_id).data[0]["id"]
    try:
        yield run_id
    finally:
        # A locked run blocks the plan delete (403), so always unlock first.
        try:
            runs_module.TestRunsAPI(get_test_jama_client).put_test_run_lock(
                run_id, False
            )
        except ResourceNotFoundException:
            pass


def test_get_test_runs_by_test_cycle(test_runs_api, real_test_cycle, real_test_run):
    response = test_runs_api.get_test_runs(params={"testCycle": real_test_cycle})
    assert real_test_run in {run["id"] for run in response.data}
    for run in response.data:
        assert {"id", "fields", "project", "itemType", "testGroup"} <= set(run)
        assert run["fields"]["testCycle"] == real_test_cycle
    assert response.meta["pageInfo"]["totalResults"] == len(response.data)


def test_get_test_runs_by_test_plan(test_runs_api, real_test_plan, real_test_run):
    response = test_runs_api.get_test_runs(params={"testPlan": real_test_plan})
    assert real_test_run in {run["id"] for run in response.data}
    assert {run["fields"]["testPlan"] for run in response.data} == {real_test_plan}


def test_get_test_runs_sorted_descending(test_runs_api, real_test_cycle):
    params = {"testCycle": real_test_cycle, "sortBy": "id.desc"}
    ids = [run["id"] for run in test_runs_api.get_test_runs(params=params).data]
    assert len(ids) > 1
    assert ids == sorted(ids, reverse=True)


def test_get_test_runs_params_untouched(test_runs_api, real_test_cycle):
    params = {"testCycle": real_test_cycle}
    test_runs_api.get_test_runs(params=params, allowed_results_per_page=2)
    assert params == {"testCycle": real_test_cycle}


def test_get_test_runs_without_filter_is_empty(test_runs_api):
    response = test_runs_api.get_test_runs()
    assert response.data == []


def test_get_test_runs_unknown_test_cycle_is_empty(test_runs_api):
    response = test_runs_api.get_test_runs(params={"testCycle": MISSING_ID})
    assert response.data == []


def test_get_test_run(
    test_runs_api,
    test_plans_api,
    real_project,
    real_test_plan,
    real_test_cycle,
    real_test_run,
):
    run = test_runs_api.get_test_run(real_test_run).data
    assert run["id"] == real_test_run
    assert run["project"] == real_project
    assert run["type"] == "testruns"
    fields = run["fields"]
    assert fields["testCycle"] == real_test_cycle
    assert fields["testPlan"] == real_test_plan
    assert {"testCase", "testRunStatus", "testRunSteps", "name"} <= set(fields)
    assert run["testGroup"][0] == real_test_cycle
    group_ids = {g["id"] for g in test_plans_api.get_test_groups(real_test_plan).data}
    assert run["testGroup"][1] in group_ids
    group_cases = test_plans_api.get_test_group_test_cases(
        real_test_plan, run["testGroup"][1]
    ).data
    assert fields["testCase"] in {case["id"] for case in group_cases}
    assert run["testCaseVersionNumber"] <= run["testCaseCurrentVersionNumber"]


def test_get_test_run_activities(test_runs_api, real_test_run):
    response = test_runs_api.get_test_run_activities(real_test_run)
    assert len(response.data) > 0
    for activity in response.data:
        assert {"id", "item", "date", "user", "action", "eventType"} <= set(activity)
        assert activity["item"] == real_test_run
    assert "BATCH_CREATE" in {activity["eventType"] for activity in response.data}


@pytest.mark.parametrize(
    "method",
    [
        "get_test_run_attachments",
        "get_test_run_comments",
        "get_test_run_downstream_related",
        "get_test_run_downstream_relationships",
        "get_test_run_upstream_related",
        "get_test_run_upstream_relationships",
        "get_test_run_links",
        "get_test_run_tags",
    ],
)
def test_get_test_run_collections(test_runs_api, real_test_run, method):
    response = getattr(test_runs_api, method)(real_test_run)
    assert isinstance(response.data, list)
    assert response.meta["pageInfo"]["totalResults"] == len(response.data)
    assert all("id" in item for item in response.data)


def test_get_test_run_lock(test_runs_api, real_test_run):
    lock = test_runs_api.get_test_run_lock(real_test_run).data
    assert isinstance(lock["locked"], bool)


def test_get_test_run_versions(test_runs_api, real_test_run):
    response = test_runs_api.get_test_run_versions(real_test_run)
    assert len(response.data) > 0
    for version in response.data:
        assert {"item", "versionNumber", "versionedItem", "createdDate"} <= set(version)
        assert version["item"] == real_test_run
        assert version["versionedItem"] == [real_test_run, version["versionNumber"]]
    assert 1 in {version["versionNumber"] for version in response.data}


def test_get_test_run_version(test_runs_api, real_test_run):
    response = test_runs_api.get_test_run_version(real_test_run, 1)
    assert response.data["item"] == real_test_run
    assert response.data["versionNumber"] == 1
    assert response.data["changeDetails"] == "Initial Creation"


def test_get_test_run_versioned_item(test_runs_api, real_project, real_test_run):
    response = test_runs_api.get_test_run_versioned_item(real_test_run, 1)
    assert response.data["id"] == real_test_run
    assert response.data["project"] == real_project
    assert response.data["version"] == 1
    assert response.data["fields"]["testRunStatus"] in {
        "NOT_RUN",
        "PASSED",
        "FAILED",
        "BLOCKED",
        "INPROGRESS",
    }


def test_get_test_run_unknown_run(test_runs_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.get_test_run(MISSING_ID)
    assert excinfo.value.status_code == 404


def test_get_test_run_tags_unknown_run(test_runs_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.get_test_run_tags(MISSING_ID)
    assert excinfo.value.status_code == 404


def test_get_test_run_tag_real_tag_not_on_run(test_runs_api, real_test_run, real_tag):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.get_test_run_tag(real_test_run, real_tag)
    assert excinfo.value.status_code == 404


def test_get_test_run_link_unknown_link(test_runs_api, real_test_run):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.get_test_run_link(real_test_run, MISSING_ID)
    assert excinfo.value.status_code == 404


def test_get_test_run_version_unknown_version(test_runs_api, real_test_run):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.get_test_run_version(real_test_run, 9999)
    assert excinfo.value.status_code == 404


def test_delete_test_run_unknown_run(test_runs_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.delete_test_run(MISSING_ID)
    assert excinfo.value.status_code == 404


def test_post_test_run_tag_unknown_run(test_runs_api, real_tag):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.post_test_run_tag(MISSING_ID, real_tag)
    assert excinfo.value.status_code == 404


def test_put_test_run(test_runs_api, scratch_test_run):
    before = test_runs_api.get_test_run(scratch_test_run).data
    body = {"fields": {"actualResults": "zz-char-put"}}
    assert test_runs_api.put_test_run(scratch_test_run, body) == 200
    after = test_runs_api.get_test_run(scratch_test_run).data
    assert after["fields"]["actualResults"] == "zz-char-put"
    assert after["fields"]["name"] == before["fields"]["name"]
    assert after["fields"]["testRunSteps"] == before["fields"]["testRunSteps"]
    versions = test_runs_api.get_test_run_versions(scratch_test_run).data
    assert len(versions) == 2
    assert (
        "Actual Results"
        in max(versions, key=lambda v: v["versionNumber"])["changeDetails"]
    )


def test_put_test_run_omitted_fields_kept(test_runs_api, scratch_test_run):
    test_runs_api.put_test_run(
        scratch_test_run, {"fields": {"actualResults": "zz-char-put"}}
    )
    steps = test_runs_api.get_test_run(scratch_test_run).data["fields"]["testRunSteps"]
    passed = [dict(step, status="PASSED") for step in steps]
    body = {"fields": {"testRunSteps": passed}}
    assert test_runs_api.put_test_run(scratch_test_run, body) == 200
    fields = test_runs_api.get_test_run(scratch_test_run).data["fields"]
    assert fields["actualResults"] == "zz-char-put"
    assert fields["testRunStatus"] == "PASSED"
    assert {step["status"] for step in fields["testRunSteps"]} == {"PASSED"}


def test_put_test_run_read_only_name_ignored(test_runs_api, scratch_test_run):
    name = test_runs_api.get_test_run(scratch_test_run).data["fields"]["name"]
    body = {"fields": {"name": "zz-char-renamed"}}
    assert test_runs_api.put_test_run(scratch_test_run, body) == 200
    fields = test_runs_api.get_test_run(scratch_test_run).data["fields"]
    assert fields["name"] == name


def test_put_test_run_without_fields_property(test_runs_api, scratch_test_run):
    with pytest.raises(APIClientException) as excinfo:
        test_runs_api.put_test_run(scratch_test_run, {})
    assert excinfo.value.status_code == 400
    assert "Property 'fields' is required for test runs" in str(excinfo.value)


def test_put_test_run_status_on_run_with_steps(test_runs_api, scratch_test_run):
    body = {"fields": {"testRunStatus": "PASSED"}}
    with pytest.raises(APIClientException) as excinfo:
        test_runs_api.put_test_run(scratch_test_run, body)
    assert excinfo.value.status_code == 400
    assert "cannot specify a status on a test run with steps" in str(excinfo.value)
    fields = test_runs_api.get_test_run(scratch_test_run).data["fields"]
    assert fields["testRunStatus"] == "NOT_RUN"


def test_patch_test_run(test_runs_api, scratch_test_run):
    patches = [
        {"op": "add", "path": "/fields/actualResults", "value": "zz-char-patched"},
        {"op": "replace", "path": "/fields/testRunSteps/0/status", "value": "FAILED"},
    ]
    assert test_runs_api.patch_test_run(scratch_test_run, patches) == 200
    fields = test_runs_api.get_test_run(scratch_test_run).data["fields"]
    assert fields["actualResults"] == "zz-char-patched"
    assert fields["testRunSteps"][0]["status"] == "FAILED"
    assert fields["testRunStatus"] == "FAILED"


def test_patch_test_run_status_on_run_with_steps(test_runs_api, scratch_test_run):
    patches = [{"op": "replace", "path": "/fields/testRunStatus", "value": "PASSED"}]
    with pytest.raises(APIClientException) as excinfo:
        test_runs_api.patch_test_run(scratch_test_run, patches)
    assert excinfo.value.status_code == 400
    assert "cannot specify a status on a test run with steps" in str(excinfo.value)
    fields = test_runs_api.get_test_run(scratch_test_run).data["fields"]
    assert fields["testRunStatus"] == "NOT_RUN"


def test_delete_test_run(test_runs_api, scratch_test_run):
    assert test_runs_api.delete_test_run(scratch_test_run) == 204
    with pytest.raises(ResourceNotFoundException):
        test_runs_api.get_test_run(scratch_test_run)
    with pytest.raises(ResourceNotFoundException):
        test_runs_api.delete_test_run(scratch_test_run)


def test_delete_test_run_while_locked(test_runs_api, scratch_test_run):
    test_runs_api.put_test_run_lock(scratch_test_run, True)
    with pytest.raises(APIClientException) as excinfo:
        test_runs_api.delete_test_run(scratch_test_run)
    assert excinfo.value.status_code == 403
    assert "currently locked" in str(excinfo.value)
    assert test_runs_api.get_test_run(scratch_test_run).data["id"] == scratch_test_run
    test_runs_api.put_test_run_lock(scratch_test_run, False)
    assert test_runs_api.delete_test_run(scratch_test_run) == 204


def test_put_test_run_lock(test_runs_api, scratch_test_run, current_user):
    assert test_runs_api.put_test_run_lock(scratch_test_run, True) == 200
    lock = test_runs_api.get_test_run_lock(scratch_test_run).data
    assert lock["locked"] is True
    assert lock["lockedBy"] == current_user["id"]
    assert "lastLockedDate" in lock
    assert test_runs_api.put_test_run_lock(scratch_test_run, False) == 200
    lock = test_runs_api.get_test_run_lock(scratch_test_run).data
    assert lock["locked"] is False
    assert "lockedBy" not in lock


def test_patch_test_run_while_locked_by_same_user(test_runs_api, scratch_test_run):
    test_runs_api.put_test_run_lock(scratch_test_run, True)
    patches = [{"op": "add", "path": "/fields/actualResults", "value": "zz-char"}]
    assert test_runs_api.patch_test_run(scratch_test_run, patches) == 200
    fields = test_runs_api.get_test_run(scratch_test_run).data["fields"]
    assert fields["actualResults"] == "zz-char"


def test_test_run_tag_round_trip(test_runs_api, scratch_test_run, real_tag):
    response = test_runs_api.post_test_run_tag(scratch_test_run, real_tag)
    assert response.meta["status"] == "Created"
    assert response.meta["id"] == real_tag
    tags = test_runs_api.get_test_run_tags(scratch_test_run).data
    assert [tag["id"] for tag in tags] == [real_tag]
    tag = test_runs_api.get_test_run_tag(scratch_test_run, real_tag).data
    assert tag["id"] == real_tag
    assert {"name", "project"} <= set(tag)
    assert test_runs_api.delete_test_run_tag(scratch_test_run, real_tag) == 204
    assert test_runs_api.get_test_run_tags(scratch_test_run).data == []


def test_post_test_run_tag_twice(test_runs_api, scratch_test_run, real_tag):
    test_runs_api.post_test_run_tag(scratch_test_run, real_tag)
    with pytest.raises(APIClientException) as excinfo:
        test_runs_api.post_test_run_tag(scratch_test_run, real_tag)
    assert excinfo.value.status_code == 400
    assert "already has the tag" in str(excinfo.value)


def test_delete_test_run_tag_not_on_run(test_runs_api, scratch_test_run, real_tag):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.delete_test_run_tag(scratch_test_run, real_tag)
    assert excinfo.value.status_code == 404


def test_test_run_link_round_trip(test_runs_api, scratch_test_run):
    url = "https://jama.example.com/widget-spec"
    response = test_runs_api.post_test_run_link(scratch_test_run, url, "Widget spec")
    assert response.meta["status"] == "Created"
    link_id = response.meta["id"]
    link = test_runs_api.get_test_run_link(scratch_test_run, link_id).data
    assert link == {"id": link_id, "url": url, "description": "Widget spec"}
    links = test_runs_api.get_test_run_links(scratch_test_run).data
    assert [item["id"] for item in links] == [link_id]
    new_url = "https://jama.example.com/widget-spec-v2"
    assert (
        test_runs_api.put_test_run_link(
            scratch_test_run, link_id, new_url, "Widget spec v2"
        )
        == 200
    )
    link = test_runs_api.get_test_run_link(scratch_test_run, link_id).data
    assert link == {"id": link_id, "url": new_url, "description": "Widget spec v2"}
    assert test_runs_api.delete_test_run_link(scratch_test_run, link_id) == 204
    assert test_runs_api.get_test_run_links(scratch_test_run).data == []


def test_delete_test_run_link_deleted_link(test_runs_api, scratch_test_run):
    link_id = test_runs_api.post_test_run_link(
        scratch_test_run, "https://jama.example.com/widget-spec", "Widget spec"
    ).meta["id"]
    test_runs_api.delete_test_run_link(scratch_test_run, link_id)
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_runs_api.delete_test_run_link(scratch_test_run, link_id)
    assert excinfo.value.status_code == 404


def test_post_test_run_updated_test_case_when_current(test_runs_api, scratch_test_run):
    run = test_runs_api.get_test_run(scratch_test_run).data
    assert run["testCaseVersionNumber"] == run["testCaseCurrentVersionNumber"]
    with pytest.raises(APIClientException) as excinfo:
        test_runs_api.post_test_run_updated_test_case(scratch_test_run)
    assert excinfo.value.status_code == 400
    assert "Test run is already up to date" in str(excinfo.value)
    versions = test_runs_api.get_test_run_versions(scratch_test_run).data
    assert [version["versionNumber"] for version in versions] == [1]


def test_test_run_attachment_link_round_trip(
    test_runs_api, scratch_test_run, real_scratch_attachment
):
    linked = False
    try:
        response = test_runs_api.post_test_run_attachment(
            scratch_test_run, real_scratch_attachment
        )
        linked = True
        assert response.meta["status"] == "Created"
        attached = test_runs_api.get_test_run_attachments(scratch_test_run).data
        assert [a["id"] for a in attached] == [real_scratch_attachment]
        status = test_runs_api.delete_test_run_attachment(
            scratch_test_run, real_scratch_attachment
        )
        linked = status != 204
        assert status == 204
        assert test_runs_api.get_test_run_attachments(scratch_test_run).data == []
    finally:
        if linked:
            try:
                test_runs_api.delete_test_run_attachment(
                    scratch_test_run, real_scratch_attachment
                )
            except Exception as error:  # noqa: BLE001
                warnings.warn(f"could not unlink the scratch attachment: {error}")


def offline_api(status_code=200):
    client = Mock()
    for verb in ("get", "post", "put", "patch", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text="",
        )
    return runs_module.TestRunsAPI(client), client


def test_status_code_methods_return_status_code():
    api, client = offline_api()
    client.delete.return_value.status_code = 204
    assert api.delete_test_run(5) == 204
    assert api.delete_test_run_link(5, 6) == 204
    assert api.delete_test_run_tag(5, 6) == 204
    assert api.delete_test_run_attachment(5, 6) == 204
    assert api.patch_test_run(5, []) == 200
    assert api.put_test_run(5, {"fields": {}}) == 200
    assert api.put_test_run_link(5, 6, "https://jama.example.com", "text") == 200
    assert api.put_test_run_lock(5, True) == 200


def test_put_test_run_sends_json_body_not_form_data():
    api, client = offline_api()
    params = {"a": 1}
    body = {"fields": {"actualResults": "text"}}
    api.put_test_run(5, body, params=params)
    args, kwargs = client.put.call_args
    assert args == ("testruns/5", params)
    assert kwargs == {"json": {"fields": {"actualResults": "text"}}}
    assert params == {"a": 1}
    assert body == {"fields": {"actualResults": "text"}}


def test_put_test_run_sends_json_strings_and_bytes_as_is():
    api, client = offline_api()
    caller = {"x-custom": "1"}
    for body in ('{"fields": {"a": "b"}}', b'{"fields": {"a": "b"}}'):
        api.put_test_run(5, body, headers=caller)
        kwargs = client.put.call_args.kwargs
        assert kwargs["content"] == body
        assert "json" not in kwargs
        assert kwargs["headers"] == {
            "x-custom": "1",
            "content-type": "application/json",
        }
    assert caller == {"x-custom": "1"}


def test_put_test_run_requires_data():
    api, client = offline_api()
    with pytest.raises(ValueError, match="data"):
        api.put_test_run(5)
    client.put.assert_not_called()


def test_patch_test_run_sends_json_patches():
    api, client = offline_api()
    patches = [{"op": "add", "path": "/fields/actualResults", "value": "x"}]
    api.patch_test_run(5, patches, params={"a": 1})
    assert client.patch.call_args.args == ("testruns/5", {"a": 1})
    assert client.patch.call_args.kwargs == {"json": patches}


def test_write_bodies():
    api, client = offline_api(201)
    api.post_test_run_link(5, "https://jama.example.com", "text")
    assert client.post.call_args.kwargs["json"] == {
        "url": "https://jama.example.com",
        "description": "text",
    }
    api.post_test_run_tag(5, 6)
    assert client.post.call_args.kwargs["json"] == {"tag": 6}
    api.post_test_run_attachment(5, 7)
    assert client.post.call_args.kwargs["json"] == {"attachment": 7}
    api.put_test_run_lock(5, False)
    assert client.put.call_args.kwargs["json"] == {"locked": False}
    api.put_test_run_link(5, 6, "https://jama.example.com", "text")
    assert client.put.call_args.args[0] == "testruns/5/links/6"


def test_updated_test_case_posts_without_body():
    api, client = offline_api(201)
    api.post_test_run_updated_test_case(5, params={"a": 1})
    assert client.post.call_args.args == ("testruns/5/updatedtestcase", {"a": 1})
    assert client.post.call_args.kwargs == {"json": None}


def test_get_test_run_passes_params_and_kwargs():
    api, client = offline_api()
    params = {"include": "data.project"}
    api.get_test_run(5, params=params, timeout=3)
    client.get.assert_called_once_with("testruns/5", params, timeout=3)
    assert params == {"include": "data.project"}


def test_get_all_methods_pass_page_size_and_params():
    client = Mock()
    client.get_all.return_value = Mock()
    api = runs_module.TestRunsAPI(client)
    params = {"testCycle": 7}
    api.get_test_runs(params=params, allowed_results_per_page=5)
    client.get_all.assert_called_with(
        "testruns", params=params, allowed_results_per_page=5
    )
    api.get_test_run_links(5, params=params, allowed_results_per_page=5)
    client.get_all.assert_called_with(
        "testruns/5/links", params=params, allowed_results_per_page=5
    )
    assert params == {"testCycle": 7}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_test_run(5),
        lambda api: api.get_test_run_lock(5),
        lambda api: api.delete_test_run(5),
        lambda api: api.patch_test_run(5, []),
        lambda api: api.put_test_run(5, {}),
        lambda api: api.post_test_run_tag(5, 6),
        lambda api: api.post_test_run_updated_test_case(5),
    ],
    ids=["get", "lock", "delete", "patch", "put", "post", "post_no_body"],
)
def test_wraps_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "post", "put", "patch", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def offline_get_all_api():
    client = Mock()
    client.get_all.return_value = Mock()
    return runs_module.TestRunsAPI(client), client


def test_get_test_runs_maps_arguments_to_query_parameters():
    api, client = offline_get_all_api()
    params = {"testCycle": [1], "a": 1}
    api.get_test_runs(
        params=params,
        test_cycle=[2],
        test_case=[3],
        test_plan=[4],
        sort_by=["name.asc"],
    )
    assert client.get_all.call_args.kwargs["params"] == {
        "testCycle": [2],
        "testCase": [3],
        "testPlan": [4],
        "sortBy": ["name.asc"],
        "a": 1,
    }
    assert params == {"testCycle": [1], "a": 1}


@pytest.mark.parametrize("key", ["testCycle", "testCase", "testPlan"])
def test_get_test_runs_accepts_a_filter_given_in_params(key):
    api, client = offline_get_all_api()
    api.get_test_runs(params={key: 5})
    assert client.get_all.call_args.kwargs["params"] == {key: 5}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_test_runs(test_cycle=[5]),
        lambda api: api.get_test_runs(test_case=[5]),
        lambda api: api.get_test_runs(test_plan=[5]),
    ],
    ids=["test_cycle", "test_case", "test_plan"],
)
def test_get_test_runs_accepts_a_filter_given_as_an_argument(call):
    api, client = offline_get_all_api()
    call(api)
    assert list(client.get_all.call_args.kwargs["params"].values()) == [[5]]


def test_get_test_run_comments_maps_root_comments_only():
    api, client = offline_get_all_api()
    params = {"rootCommentsOnly": False}
    api.get_test_run_comments(5, params=params, root_comments_only=True)
    assert client.get_all.call_args.kwargs["params"] == {"rootCommentsOnly": True}
    assert params == {"rootCommentsOnly": False}
    api.get_test_run_comments(5)
    assert client.get_all.call_args.kwargs["params"] is None


def test_put_test_run_caller_header_overrides_case_insensitively():
    client = Mock()
    client.put.return_value.status_code = 200
    runs_module.TestRunsAPI(client).put_test_run(
        5, '{"fields": {}}', headers={"Content-Type": "text/plain"}
    )
    headers = client.put.call_args.kwargs["headers"]
    assert headers.get_list("content-type") == ["text/plain"]
