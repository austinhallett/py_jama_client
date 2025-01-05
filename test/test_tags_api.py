from py_jama_client.apis.tags_api import TagsAPI


def test_get_tags(get_test_jama_client):
    tags_api = TagsAPI(get_test_jama_client)
    response = tags_api.get_tags(project_id=195)
    assert response.data != []


def test_get_tag(get_test_jama_client):
    tags_api = TagsAPI(get_test_jama_client)
    response = tags_api.get_tag(tag_id=1)
    assert response.data is not None


def test_get_tag_items(get_test_jama_client):
    tags_api = TagsAPI(get_test_jama_client)
    response = tags_api.get_tag_items(tag_id=1)
    assert response.data != []
