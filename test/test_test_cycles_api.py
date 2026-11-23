from unittest.mock import Mock

import pytest

from py_jama_client.apis import test_cycles_api as cycles_module
from py_jama_client.apis import test_plans_api as plans_module
from py_jama_client.exceptions import (
    APIClientException,
    APIException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ID = 2147483647


@pytest.fixture(scope="function")
def test_cycles_api(get_test_jama_client):
    return cycles_module.TestCyclesAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def test_plans_api(get_test_jama_client):
    return plans_module.TestPlansAPI(get_test_jama_client)


@pytest.fixture(scope="function")
def scratch_test_cycle(test_plans_api, scratch_test_plan, real_test_case):
    # Deleting the scratch plan also deletes its cycles and runs,
    # so no separate cycle teardown is needed.
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    test_plans_api.post_test_group_test_case(
        scratch_test_plan, group_id, real_test_case
    )
    return test_plans_api.post_testplans_testcycles(
        scratch_test_plan,
        "zz-char-cycle",
        "2026-01-05",
        "2026-01-30",
        testgroups_to_include=[group_id],
    ).meta["id"]


def group_id_named(test_plans_api, plan_id, name):
    groups = test_plans_api.get_test_groups(plan_id).data
    group_id = next((group["id"] for group in groups if group["name"] == name), None)
    if group_id is None:
        pytest.fail(f"no group {name!r} in plan {plan_id}")
    return group_id


def test_get_test_cycle(test_cycles_api, real_project, real_test_plan, real_test_cycle):
    response = test_cycles_api.get_test_cycle(real_test_cycle)
    cycle = response.data
    assert cycle["id"] == real_test_cycle
    assert cycle["project"] == real_project
    assert cycle["fields"]["testPlan"] == real_test_plan
    assert {"name", "startDate", "endDate"} <= set(cycle["fields"])
    assert cycle["fields"]["startDate"] <= cycle["fields"]["endDate"]


def test_get_test_cycle_runs(test_cycles_api, real_test_cycle):
    runs = test_cycles_api.get_test_cycle_runs(real_test_cycle).data
    assert len(runs) > 0
    for run in runs:
        assert {"id", "fields", "project"} <= set(run)
        assert run["fields"]["testCycle"] == real_test_cycle
    assert len({run["id"] for run in runs}) == len(runs)


def test_get_test_cycle_test_group(
    test_cycles_api, test_plans_api, real_test_plan, real_test_cycle
):
    group_id = group_id_named(test_plans_api, real_test_plan, "Mounting Tests")
    response = test_cycles_api.get_test_cycle_test_group(real_test_cycle, group_id)
    assert response.data["testGroup"] == group_id
    assert response.data["testCycle"] == real_test_cycle
    assert response.data["name"] == "Mounting Tests"
    assert response.data["type"] == "testcycletestgroups"


def test_get_test_cycle_versions(test_cycles_api, real_test_cycle):
    response = test_cycles_api.get_test_cycle_versions(real_test_cycle)
    assert len(response.data) > 0
    for version in response.data:
        assert {"item", "versionNumber", "versionedItem", "createdDate"} <= set(version)
        assert version["item"] == real_test_cycle
        assert version["versionedItem"] == [real_test_cycle, version["versionNumber"]]
    assert 1 in {version["versionNumber"] for version in response.data}


def test_get_test_cycle_version(test_cycles_api, real_test_cycle):
    response = test_cycles_api.get_test_cycle_version(real_test_cycle, 1)
    assert response.data["item"] == real_test_cycle
    assert response.data["versionNumber"] == 1


def test_get_test_cycle_versioned_item(
    test_cycles_api, real_project, real_test_plan, real_test_cycle
):
    response = test_cycles_api.get_test_cycle_versioned_item(real_test_cycle, 1)
    assert response.data["id"] == real_test_cycle
    assert response.data["project"] == real_project
    assert response.data["fields"]["testPlan"] == real_test_plan


def test_get_test_cycle_unknown_cycle(test_cycles_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_cycles_api.get_test_cycle(MISSING_ID)
    assert excinfo.value.status_code == 404


def test_get_test_cycle_versions_unknown_cycle(test_cycles_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_cycles_api.get_test_cycle_versions(MISSING_ID)
    assert excinfo.value.status_code == 404


def test_get_test_cycle_test_group_unknown_group_on_real_cycle(
    test_cycles_api, real_test_cycle
):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_cycles_api.get_test_cycle_test_group(real_test_cycle, MISSING_ID)
    assert excinfo.value.status_code == 404


def test_get_test_cycle_test_group_group_of_other_plan(
    test_cycles_api, test_plans_api, real_test_cycle, scratch_test_plan
):
    group_id = test_plans_api.post_test_group(scratch_test_plan, "zz-char-group").meta[
        "id"
    ]
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_cycles_api.get_test_cycle_test_group(real_test_cycle, group_id)
    assert excinfo.value.status_code == 404


def test_get_test_cycle_version_unknown_version(test_cycles_api, real_test_cycle):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_cycles_api.get_test_cycle_version(real_test_cycle, 9999)
    assert excinfo.value.status_code == 404


def test_delete_test_cycle_unknown_cycle(test_cycles_api):
    with pytest.raises(ResourceNotFoundException) as excinfo:
        test_cycles_api.delete_test_cycle(MISSING_ID)
    assert excinfo.value.status_code == 404


def test_patch_test_cycle(test_cycles_api, scratch_test_cycle):
    patches = [{"op": "replace", "path": "/fields/name", "value": "zz-char-patched"}]
    assert test_cycles_api.patch_test_cycle(scratch_test_cycle, patches) == 200
    fields = test_cycles_api.get_test_cycle(scratch_test_cycle).data["fields"]
    assert fields["name"] == "zz-char-patched"
    assert (fields["startDate"], fields["endDate"]) == ("2026-01-05", "2026-01-30")


def test_put_test_cycle(test_cycles_api, scratch_test_cycle):
    new_fields = {
        "name": "zz-char-put",
        "startDate": "2026-02-02",
        "endDate": "2026-02-27",
    }
    assert test_cycles_api.put_test_cycle(scratch_test_cycle, new_fields) == 200
    fields = test_cycles_api.get_test_cycle(scratch_test_cycle).data["fields"]
    assert fields["name"] == "zz-char-put"
    assert (fields["startDate"], fields["endDate"]) == ("2026-02-02", "2026-02-27")
    versions = test_cycles_api.get_test_cycle_versions(scratch_test_cycle).data
    assert len(versions) == 2


def test_put_test_cycle_omitted_dates(test_cycles_api, scratch_test_cycle):
    with pytest.raises(APIClientException) as excinfo:
        test_cycles_api.put_test_cycle(scratch_test_cycle, {"name": "zz-char-put"})
    assert excinfo.value.status_code == 400
    assert "required fields. fields: startDate, endDate" in str(excinfo.value)
    fields = test_cycles_api.get_test_cycle(scratch_test_cycle).data["fields"]
    assert fields["name"] == "zz-char-cycle"


def test_delete_test_cycle(test_cycles_api, scratch_test_cycle):
    runs = test_cycles_api.get_test_cycle_runs(scratch_test_cycle).data
    assert len(runs) == 1
    assert test_cycles_api.delete_test_cycle(scratch_test_cycle) == 204
    with pytest.raises(ResourceNotFoundException):
        test_cycles_api.get_test_cycle(scratch_test_cycle)
    with pytest.raises(ResourceNotFoundException):
        test_cycles_api.get_test_cycle_runs(scratch_test_cycle)


def offline_api(status_code=200):
    client = Mock()
    for verb in ("get", "put", "patch", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code, json=Mock(return_value={"data": {}, "meta": {}})
        )
    return cycles_module.TestCyclesAPI(client), client


def test_status_code_methods_return_status_code():
    api, client = offline_api()
    client.delete.return_value.status_code = 204
    assert api.delete_test_cycle(5) == 204
    assert api.patch_test_cycle(5, [{"op": "remove", "path": "/fields/x"}]) == 200
    assert api.put_test_cycle(5, {"name": "cycle"}) == 200


def test_put_and_patch_params_and_bodies_untouched():
    api, client = offline_api()
    params = {"a": 1}
    fields = {"name": "cycle"}
    patches = [{"op": "replace", "path": "/fields/name", "value": "x"}]
    api.put_test_cycle(5, fields, params=params)
    api.patch_test_cycle(5, patches, params=params)
    assert params == {"a": 1}
    assert fields == {"name": "cycle"}
    assert client.put.call_args.kwargs["json"] == {"fields": {"name": "cycle"}}
    assert client.patch.call_args.kwargs["json"] == patches


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_test_cycle(5),
        lambda api: api.get_test_cycle_test_group(5, 6),
        lambda api: api.get_test_cycle_version(5, 1),
        lambda api: api.get_test_cycle_versioned_item(5, 1),
        lambda api: api.delete_test_cycle(5),
        lambda api: api.patch_test_cycle(5, []),
        lambda api: api.put_test_cycle(5, {}),
    ],
    ids=["cycle", "group", "version", "versioned_item", "delete", "patch", "put"],
)
def test_wraps_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "put", "patch", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_put_test_cycle_maps_test_run_generation_config():
    api, client = offline_api()
    config = {"testGroupsToInclude": [1, 2]}
    api.put_test_cycle(5, {"name": "cycle"}, test_run_generation_config=config)
    assert client.put.call_args.kwargs["json"] == {
        "fields": {"name": "cycle"},
        "testRunGenerationConfig": config,
    }
    api.put_test_cycle(5, {"name": "cycle"})
    assert client.put.call_args.kwargs["json"] == {"fields": {"name": "cycle"}}
