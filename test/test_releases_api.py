from datetime import datetime
from unittest.mock import Mock

import pytest

from py_jama_client.apis import ReleasesAPI
from py_jama_client.exceptions import APIException, CoreException


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


def test_post_release(releases_api, real_project, resolved):
    # Creates MockRelease<N>, which the API cannot delete.
    name = resolved("scratch_release_name")
    description = "Scratch release for API tests."
    response = releases_api.post_release(
        name, datetime(2026, 1, 1), real_project, description
    )
    assert response.meta["status"] == "Created"
    release = releases_api.get_release(response.meta["id"]).data
    assert (release["name"], release["project"], release["description"]) == (
        name,
        real_project,
        description,
    )
    assert release["releaseDate"].startswith("2026-01-01")


def test_put_release_round_trip(releases_api, real_release):
    original = releases_api.get_release(real_release).data
    date = datetime.strptime(original["releaseDate"][:10], "%Y-%m-%d")

    def put(description):
        return releases_api.put_release(
            real_release, original["name"], date, original["project"], description
        )

    try:
        assert put("zz-char description").meta["status"] == "OK"
        changed = releases_api.get_release(real_release).data
        assert changed["description"] == "zz-char description"
    finally:
        put(original["description"])
    restored = releases_api.get_release(real_release).data
    assert {k: restored[k] for k in ("name", "description", "releaseDate")} == {
        k: original[k] for k in ("name", "description", "releaseDate")
    }


def offline_api():
    client = Mock()
    for verb in ("get", "post", "put"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
        )
    return ReleasesAPI(client), client


def test_get_releases_merges_project_into_caller_params():
    api, client = offline_api()
    api.get_releases(7, params={"include": "project"})
    assert client.get_all.call_args.args[1] == {"include": "project", "project": 7}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_release(5),
        lambda api: api.post_release("n", datetime(2026, 1, 1), 7),
        lambda api: api.put_release(5, "n", datetime(2026, 1, 1), 7),
    ],
    ids=["get", "post", "put"],
)
def test_releases_wrap_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "post", "put"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


@pytest.mark.parametrize(
    ("method", "args", "verb"),
    [
        ("get_releases", (1,), "get_all"),
        ("get_release", (1,), "get"),
    ],
)
def test_release_reads_pass_kwargs_to_the_client(method, args, verb):
    client = Mock()
    getattr(client, verb).return_value.status_code = 200
    getattr(ReleasesAPI(client), method)(*args, timeout=3, headers={"x-custom": "1"})
    kwargs = getattr(client, verb).call_args.kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["headers"] == {"x-custom": "1"}
