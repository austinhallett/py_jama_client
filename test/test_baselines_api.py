def test_get_baselines(get_test_jama_client):
    response = get_test_jama_client.get_baselines(project_id=82)
    assert response.data is not None
