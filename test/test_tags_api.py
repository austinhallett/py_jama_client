from py_jama_client.apis.tags_api import TagsAPI


def test_get_tags(get_test_jama_client, real_project):
    tags_api = TagsAPI(get_test_jama_client)
    response = tags_api.get_tags(project_id=real_project)
    assert response.data != []


def test_get_tag(get_test_jama_client, real_tag):
    tags_api = TagsAPI(get_test_jama_client)
    response = tags_api.get_tag(tag_id=real_tag)
    assert response.data is not None


def test_get_tag_items(get_test_jama_client, real_tag):
    tags_api = TagsAPI(get_test_jama_client)
    response = tags_api.get_tag_items(tag_id=real_tag)
    assert response.data != []
