from py_jama_client.apis.baselines_api import BaselinesAPI


def test_get_baselines(get_test_jama_client, real_project):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baselines(project_id=real_project)
    assert response.data is not None


def test_get_baseline(get_test_jama_client, real_baseline):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baseline(baseline_id=real_baseline)
    assert response.data is not None


def test_get_baseline_review_link(get_test_jama_client, real_baseline):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baseline_review_link(
        baseline_id=real_baseline)
    assert response.data is not None


def test_get_baseline_versioned_items(get_test_jama_client, real_baseline):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baseline_versioned_items(
        baseline_id=real_baseline)
    assert response.data is not None


def test_get_baseline_versioned_item(get_test_jama_client,
                                     real_baseline,
                                     real_baseline_versioned_item):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baseline_versioned_item(
        baseline_id=real_baseline,
        item_id=real_baseline_versioned_item)
    assert response.data is not None


def test_get_baseline_versioned_item_relationships(
        get_test_jama_client,
        real_baseline,
        real_baseline_versioned_item):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baseline_versioned_item_relationships(
        baseline_id=real_baseline,
        item_id=real_baseline_versioned_item)
    assert response.data is not None


def test_get_baselines_with_link(get_test_jama_client, real_project):
    baselines_api = BaselinesAPI(get_test_jama_client)
    response = baselines_api.get_baselines(
        project_id=real_project,
        params={"include": ("data.project", "data.createdBy")},
    )
    assert len(response.linked) > 0
