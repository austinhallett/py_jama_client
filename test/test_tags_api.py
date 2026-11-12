import pytest

from py_jama_client.apis.tags_api import TagsAPI


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


@pytest.fixture(scope="function")
def populated_tag_item(tags_api, real_project):
    for tag in tags_api.get_tags(project_id=real_project).data:
        items = tags_api.get_tag_items(tag_id=tag["id"]).data
        if items:
            return tag["id"], items[0]["id"]
    pytest.skip("No populated tag is available in the sample project.")


def test_get_tag_items(tags_api, populated_tag_item):
    tag_id, item_id = populated_tag_item
    response = tags_api.get_tag_items(tag_id=tag_id)
    assert item_id in {item["id"] for item in response.data}
