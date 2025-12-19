from py_jama_client.apis import ReleasesAPI
import pytest


@pytest.fixture(scope="function")
def releases_api(get_test_jama_client) -> ReleasesAPI:
    api_instance = ReleasesAPI(get_test_jama_client)
    return api_instance


def test_get_releases(releases_api, real_project):
    response = releases_api.get_releases(project_id=real_project)
    assert response.data != []


def test_get_release(releases_api, real_release):
    response = releases_api.get_release(release_id=real_release)
    assert response.data != []
