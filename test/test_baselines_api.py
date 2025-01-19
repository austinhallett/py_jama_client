from py_jama_client.apis.baselines_api import BaselinesAPI
import pytest

@pytest.fixture(scope="function")
def baselines_api(get_test_jama_client):
    api_instance = BaselinesAPI(get_test_jama_client)
    return api_instance


def test_get_baselines(baselines_api, real_project):
    response = baselines_api.get_baselines(project_id=real_project)
    assert response.data is not None


def test_get_baseline(baselines_api, real_baseline):
    response = baselines_api.get_baseline(baseline_id=real_baseline)
    assert response.data is not None


def test_get_baseline_review_link(baselines_api, real_baseline):
    response = baselines_api.get_baseline_review_link(
        baseline_id=real_baseline)
    assert response.data is not None


def test_get_baseline_versioned_items(baselines_api, real_baseline):
    response = baselines_api.get_baseline_versioned_items(
        baseline_id=real_baseline)
    assert response.data is not None


def test_get_baseline_versioned_item(baselines_api,
                                     real_baseline,
                                     real_baseline_versioned_item):
    response = baselines_api.get_baseline_versioned_item(
        baseline_id=real_baseline,
        item_id=real_baseline_versioned_item)
    assert response.data is not None


def test_get_baseline_versioned_item_relationships(
                                        baselines_api,
                                        real_baseline,
                                        real_baseline_versioned_item):
    response = baselines_api.get_baseline_versioned_item_relationships(
        baseline_id=real_baseline,
        item_id=real_baseline_versioned_item)
    assert response.data is not None


def test_get_baselines_with_link(baselines_api, real_project):
    response = baselines_api.get_baselines(
        project_id=real_project,
        params={"include": ("data.project", "data.createdBy")},
    )
    assert len(response.linked) > 0
