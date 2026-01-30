from py_jama_client.apis.relationships_api import RelationshipsAPI
import pytest


@pytest.fixture(scope="function")
def relationships_api(get_test_jama_client):
    api_instance = RelationshipsAPI(get_test_jama_client)
    return api_instance


def test_get_relationships(relationships_api, real_project):
    response = relationships_api.get_relationships(project_id=real_project)
    assert response.data != []


def test_get_all_lastid(relationships_api, real_project):
    resource_path = "relationships"
    params = {"project": real_project,
              "maxResults": 1}
    response = relationships_api.client.get(resource_path, params=params)
    if (response.status_code == 400 and
            "lastId parameter is now required" in response.text):
        response = relationships_api.get_all_lastid(
            resource_path=resource_path,
            params={"project": real_project})
    else:
        pytest.skip("lastId parameter is not required by test Jama instance.")
    assert response.data != []


def test_get_page_lastid(relationships_api, real_project):
    resource_path = "relationships"
    params = {"project": real_project,
              "maxResults": 1}
    response = relationships_api.client.get(resource_path, params=params)
    if (response.status_code == 400 and
            "lastId parameter is now required" in response.text):
        response = relationships_api.get_page_lastid(
            resource_path=resource_path,
            last_id=0,
            params={"project": real_project})
    else:
        pytest.skip("lastId parameter is not required by test Jama instance.")
    assert response.data != []


def test_get_relationship(relationships_api, real_relationship):
    response = relationships_api.get_relationship(
        relationship_id=real_relationship)
    assert response.data != []


def test_get_relationship_types(relationships_api):
    response = relationships_api.get_relationship_types()
    assert response.data != []


def test_get_relationship_type(relationships_api, real_relationship_type):
    response = relationships_api.get_relationship_type(
        relationship_type_id=real_relationship_type
    )
    assert response.data != []
