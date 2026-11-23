from unittest.mock import Mock

import pytest

from py_jama_client.apis.baselines_api import BaselinesAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
)


@pytest.fixture(scope="function")
def baselines_api(get_test_jama_client):
    api_instance = BaselinesAPI(get_test_jama_client)
    return api_instance


def test_get_baselines(baselines_api, real_project, real_baseline):
    response = baselines_api.get_baselines(project_id=real_project)
    assert str(real_baseline) in {str(baseline["id"]) for baseline in response.data}


def test_get_baseline(baselines_api, real_baseline):
    response = baselines_api.get_baseline(baseline_id=real_baseline)
    assert str(response.data["id"]) == str(real_baseline)


def test_get_baseline_review_link_without_review(baselines_api, real_baseline):
    with pytest.raises(ResourceNotFoundException) as error:
        baselines_api.get_baseline_review_link(baseline_id=real_baseline)
    assert error.value.reason
    assert "Review not found for this baseline" in error.value.reason


def test_get_baseline_versioned_items(
    baselines_api, real_baseline, real_baseline_versioned_item, bounded_pages
):
    bounded_pages["result_limit"] = 4
    response = baselines_api.get_baseline_versioned_items(baseline_id=real_baseline)
    assert len(response.data) == 4
    assert str(real_baseline_versioned_item) in {
        str(item["id"]) for item in response.data
    }


def test_get_baseline_versioned_item(
    baselines_api, real_baseline, real_baseline_versioned_item
):
    response = baselines_api.get_baseline_versioned_item(
        baseline_id=real_baseline, item_id=real_baseline_versioned_item
    )
    assert str(response.data["id"]) == str(real_baseline_versioned_item)


def test_get_baseline_versioned_item_relationships(
    baselines_api, real_baseline, real_baseline_versioned_item
):
    response = baselines_api.get_baseline_versioned_item_relationships(
        baseline_id=real_baseline, item_id=real_baseline_versioned_item
    )
    assert response.data
    for relationship in response.data:
        assert {"fromItem", "toItem", "relationshipType"} <= relationship.keys()
        assert str(real_baseline_versioned_item) in {
            str(relationship["fromItem"][0]),
            str(relationship["toItem"][0]),
        }


def test_get_baselines_with_link(baselines_api, real_project):
    response = baselines_api.get_baselines(
        project_id=real_project,
        params={"include": ("data.project", "data.createdBy")},
    )
    assert len(response.linked) > 0


def test_get_baseline_review_link_synthetic(get_test_jama_client):
    response = BaselinesAPI(get_test_jama_client).get_baseline_review_link(
        baseline_id=1
    )
    assert response.data["url"].startswith("https://jama.example.com")
    assert response.data["reviewKey"] == "REVIEW-1"
    assert response.data["reviewName"] == "Review 1"
    assert response.data["revisionId"] == 1
    assert response.data["deleted"] is False
    assert response.data["readAccess"] is True


def test_put_baseline(baselines_api, resolved):
    baseline_id = resolved("scratch_baseline")
    original = baselines_api.get_baseline(baseline_id).data
    response = baselines_api.put_baseline(
        baseline_id,
        original["source"],
        "ITEM",
        original["origin"]["item"],
        "zz-char baseline",
        "zz-char description",
    )
    assert response.meta["status"] == "OK"
    changed = baselines_api.get_baseline(baseline_id).data
    assert (changed["name"], changed["description"]) == (
        "zz-char baseline",
        "zz-char description",
    )


def test_delete_baseline(baselines_api, resolved):
    # No API creates a baseline; this deletes a scratch one made for it.
    baseline_id = resolved("scratch_baseline")
    assert baselines_api.delete_baseline(baseline_id) == 204
    with pytest.raises(ResourceNotFoundException):
        baselines_api.get_baseline(baseline_id)


def offline_api(status_code=200, text=""):
    client = Mock()
    for verb in ("get", "put", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=status_code,
            json=Mock(return_value={"data": {}, "meta": {}}),
            text=text,
        )
    return BaselinesAPI(client), client


def test_put_baseline_sends_json_body():
    api, client = offline_api()
    api.put_baseline(1, 7, "BASELINE", 5, "Baseline 1", "Description 1", 20)
    client.put.assert_called_with(
        "baselines/1",
        json={
            "source": 7,
            "baselineOriginType": "BASELINE",
            "baselineOriginId": 5,
            "name": "Baseline 1",
            "description": "Description 1",
            "baselineStatusPickListOption": 20,
        },
    )


def test_delete_baseline_returns_status_code():
    api, client = offline_api(204)
    assert api.delete_baseline(1) == 204
    client.delete.assert_called_with("baselines/1")


def test_delete_baseline_raises_on_error_status():
    api, _ = offline_api(404, '{"meta": {"message": "Not found"}}')
    with pytest.raises(ResourceNotFoundException):
        api.delete_baseline(1)


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_baseline(1),
        lambda api: api.put_baseline(1, 7, "BASELINE", 5, "a", "b", 20),
        lambda api: api.delete_baseline(1),
        lambda api: api.get_baseline_review_link(1),
        lambda api: api.get_baseline_versioned_item(1, 2),
    ],
    ids=["get", "put", "delete", "review_link", "versioned_item"],
)
def test_baseline_calls_wrap_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_baselines_maps_source_and_created_by():
    api, client = offline_api()
    client.get_all = Mock()
    params = {"source": 1}
    api.get_baselines(5, params=params, source=7, created_by=8)
    assert get_all_params(client) == {"project": 5, "source": 7, "createdBy": 8}
    assert params == {"source": 1}


def test_get_baselines_sends_no_new_parameters_by_default():
    api, client = offline_api()
    client.get_all = Mock()
    api.get_baselines(5)
    assert get_all_params(client) == {"project": 5}


def test_get_baseline_versioned_items_maps_categories():
    api, client = offline_api()
    client.get_all = Mock()
    params = {"categories": False}
    api.get_baseline_versioned_items(5, params=params, categories=True)
    assert get_all_params(client) == {"categories": True}
    assert params == {"categories": False}
    api.get_baseline_versioned_items(5)
    assert get_all_params(client) is None
