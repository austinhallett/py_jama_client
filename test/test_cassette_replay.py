import pytest

from py_jama_client.apis.tags_api import TagsAPI
from py_jama_client.exceptions import ResourceNotFoundException


def test_tags_round_trip_through_jama_client(get_test_jama_client):
    tags = TagsAPI(get_test_jama_client)

    listed = tags.get_tags(project_id=1, allowed_results_per_page=2)
    created = tags.post_tag(name="Tag D", project=1)
    with pytest.raises(ResourceNotFoundException):
        tags.get_tag(tag_id=99)

    assert [tag["name"] for tag in listed.data] == ["Tag A", "Tag B", "Tag C"]
    assert created.meta["id"] == 14
