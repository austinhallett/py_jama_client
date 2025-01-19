from py_jama_client.apis.projects_api import ProjectsAPI


def test_get_projects(get_test_jama_client):
    projects_api = ProjectsAPI(get_test_jama_client)
    response = projects_api.get_projects()
    assert response.data != []


def test_get_project_by_id(get_test_jama_client, real_project):
    projects_api = ProjectsAPI(get_test_jama_client)
    response = projects_api.get_project_by_id(project_id=real_project)
    assert response.data is not None
