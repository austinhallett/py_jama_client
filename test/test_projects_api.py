from py_jama_client.apis.projects_api import ProjectsAPI
import pytest

@pytest.fixture(scope="function")
def projects_api(get_test_jama_client):
    api_instance = ProjectsAPI(get_test_jama_client)
    return api_instance


def test_get_projects(projects_api):
    response = projects_api.get_projects()
    assert response.data != []


def test_get_project_by_id(projects_api, real_project):
    response = projects_api.get_project_by_id(project_id=real_project)
    assert response.data is not None
