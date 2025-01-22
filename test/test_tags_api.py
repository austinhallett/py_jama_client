from py_jama_client.apis.tags_api import TagsAPI
import pytest

@pytest.fixture(scope="function")
def tags_api(get_test_jama_client):
    api_instance = TagsAPI(get_test_jama_client)
    return api_instance


def test_get_tags(tags_api, real_project):
    response = tags_api.get_tags(project_id=real_project)
    assert response.data != []


def test_get_tag(tags_api, real_tag):
    response = tags_api.get_tag(tag_id=real_tag)
    assert response.data is not None


def test_get_tag_items(tags_api, real_tag):
    response = tags_api.get_tag_items(tag_id=real_tag)
    assert response.data != []
