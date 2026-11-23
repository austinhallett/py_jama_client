from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from py_jama_client.apis.abstract_items_api import AbstractItemsAPI
from py_jama_client.apis.activities_api import ActivitiesAPI
from py_jama_client.apis.baselines_api import BaselinesAPI
from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.apis.releases_api import ReleasesAPI
from py_jama_client.apis.tags_api import TagsAPI
from py_jama_client.client import JamaClient
from py_jama_client.exceptions import (
    APIClientException,
    APIException,
    APIServerException,
    CoreException,
    ResourceNotFoundException,
    UnauthorizedException,
)


def make_client(handler, oauth=False):
    client = JamaClient.__new__(JamaClient)
    client._host_name = "https://jama.example.com/rest/v1/"
    client._credentials = ("id", "secret")
    client._oauth = oauth
    client._token = "tok-123"
    client._session = httpx.Client(transport=httpx.MockTransport(handler))
    if oauth:
        client._check_oauth_token = lambda: None
    return client


def test_get_all_keeps_data_when_page_info_missing():
    def handler(request):
        return httpx.Response(200, json={"meta": {}, "data": [{"id": 1}, {"id": 2}]})

    client = make_client(handler)
    result = client.get_all("items")
    client.close()

    assert result.data == [{"id": 1}, {"id": 2}]


def test_get_all_advances_by_rows_returned_when_server_caps_page_size():
    rows = [{"id": i} for i in range(5)]
    starts = []

    def handler(request):
        start = int(request.url.params["startAt"])
        starts.append((start, int(request.url.params["maxResults"])))
        page = rows[start : start + 2]
        page_info = {
            "startIndex": start,
            "resultCount": len(page),
            "totalResults": len(rows),
        }
        return httpx.Response(200, json={"meta": {"pageInfo": page_info}, "data": page})

    client = make_client(handler)
    result = client.get_all("items", allowed_results_per_page=5)
    client.close()

    assert result.data == rows
    assert starts == [(0, 5), (2, 5), (4, 5)]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(404, json={"data": "x"}),
        httpx.Response(404, json=None),
        httpx.Response(404, json=["not", "a", "dict"]),
        httpx.Response(404, json={"meta": None}),
        httpx.Response(404, text="not json"),
    ],
)
def test_404_without_meta_message_raises_mapped_exception(response):
    with pytest.raises(ResourceNotFoundException) as info:
        JamaClient.handle_response_status(response)
    assert info.value.status_code == 404


def test_401_and_400_without_meta_raise_mapped_exceptions():
    with pytest.raises(UnauthorizedException):
        JamaClient.handle_response_status(httpx.Response(401, json={"error": "x"}))
    with pytest.raises(APIClientException):
        JamaClient.handle_response_status(httpx.Response(400, json=None))


def test_500_without_meta_raises_server_exception():
    with pytest.raises(APIServerException):
        JamaClient.handle_response_status(httpx.Response(500, json={"oops": 1}))


@pytest.mark.parametrize(
    "verb", ["get", "post", "put", "patch", "delete", "delete_with_body"]
)
def test_caller_headers_dict_is_not_mutated_with_oauth(verb):
    seen = []

    def handler(request):
        seen.append(request.headers.get("authorization"))
        return httpx.Response(200, json={})

    client = make_client(handler, oauth=True)
    headers = {"x-custom": "1"}
    if verb == "delete_with_body":
        getattr(client, verb)("items/1", {"a": 1}, headers=headers)
    else:
        getattr(client, verb)("items/1", headers=headers)
    client.close()

    assert headers == {"x-custom": "1"}
    assert seen == ["Bearer" + " tok-123"]


@pytest.mark.parametrize("message", [123, ["x"], {"a": 1}, None, ""])
def test_non_string_meta_message_becomes_no_response(message):
    response = httpx.Response(404, json={"meta": {"message": message}})
    with pytest.raises(ResourceNotFoundException) as info:
        JamaClient.handle_response_status(response)
    assert info.value.reason == "No Response"


def test_message_missing_from_meta_becomes_no_response():
    with pytest.raises(ResourceNotFoundException) as info:
        JamaClient.handle_response_status(httpx.Response(404, json={"meta": {}}))
    assert info.value.reason == "No Response"


def json_null_response(status):
    return httpx.Response(
        status, content=b"null", headers={"content-type": "application/json"}
    )


def test_404_with_json_null_body_raises_mapped_exception():
    with pytest.raises(ResourceNotFoundException):
        JamaClient.handle_response_status(json_null_response(404))


def test_get_all_with_json_null_body_raises_mapped_exception():
    client = make_client(lambda request: json_null_response(404))
    with pytest.raises(ResourceNotFoundException):
        client.get_all("items")
    client.close()


@pytest.mark.parametrize(
    "call",
    [
        lambda p: ActivitiesAPI(Mock()).get_admin_activities(
            filter_term="x", project_id=1, params=p
        ),
        lambda p: ActivitiesAPI(Mock()).get_activities(1, params=p),
        lambda p: AbstractItemsAPI(Mock()).get_abstract_items(
            project=1, item_type=2, sort_by="name.asc", params=p
        ),
        lambda p: AbstractItemsAPI(Mock()).get_abstract_item_versions(5, params=p),
        lambda p: RelationshipsAPI(Mock()).get_relationships(1, params=p),
        lambda p: BaselinesAPI(Mock()).get_baselines(1, params=p),
        lambda p: TagsAPI(Mock()).get_tags(1, params=p),
        lambda p: ReleasesAPI(Mock()).get_releases(1, params=p),
        lambda p: ItemsAPI(Mock()).get_items(1, params=p),
    ],
    ids=[
        "admin_activities",
        "activities",
        "abstract_items",
        "abstract_item_versions",
        "relationships",
        "baselines",
        "tags",
        "releases",
        "items",
    ],
)
def test_list_methods_leave_the_callers_params_alone(call):
    params = {"keep": "me"}
    call(params)
    assert params == {"keep": "me"}


@pytest.mark.parametrize("oauth", [False, True])
def test_get_available_endpoints_uses_the_clients_auth(oauth):
    seen = []

    def handler(request):
        seen.append(request.headers["authorization"])
        return httpx.Response(200, json={"meta": {}, "data": []})

    client = make_client(handler, oauth=oauth)
    client.get_available_endpoints()
    client.close()

    basic = httpx.BasicAuth("id", "secret")._auth_header
    scheme = "Bear" + "er "
    assert seen == [scheme + "tok-123" if oauth else basic]


def refuse_connection(request):
    raise httpx.ConnectError("connection refused", request=request)


@pytest.mark.parametrize("oauth", [False, True])
@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.get("items"),
        lambda c: c.post("items", json={}),
        lambda c: c.put("items/1", json={}),
        lambda c: c.patch("items/1", json=[]),
        lambda c: c.delete("items/1"),
        lambda c: c.delete_with_body("items/1/tags", {}),
    ],
)
def test_transport_errors_become_core_exceptions(call, oauth):
    client = make_client(refuse_connection, oauth=oauth)
    with pytest.raises(CoreException) as caught:
        call(client)
    assert isinstance(caught.value.__cause__, httpx.ConnectError)
    client.close()


def test_api_methods_raise_api_exception_on_transport_errors():
    client = make_client(refuse_connection)
    with pytest.raises(APIException):
        ItemsAPI(client).get_item(1)
    client.close()


def test_extra_positional_arguments_are_rejected():
    with pytest.raises(TypeError):
        arguments: tuple[Any, ...] = (375, {"maxResults": 1})
        TagsAPI(Mock()).get_tags(*arguments)


def test_path_ids_cannot_change_the_endpoint():
    seen = []

    def handler(request):
        seen.append(request.url.raw_path.decode())
        return httpx.Response(200, json={"meta": {}, "data": {"id": 5}})

    client = make_client(handler)
    item_id: Any = "1/../../users/5"
    ItemsAPI(client).get_item(item_id)
    client.close()
    assert seen == ["/rest/v1/items/1%2F..%2F..%2Fusers%2F5"]


def test_api_paths_encode_every_interpolated_value():
    import ast
    from pathlib import Path

    import py_jama_client.apis

    allowed = {"self.resource_path"}
    raw = []
    for path in Path(py_jama_client.apis.__file__).parent.glob("*_api.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.JoinedStr):
                continue
            literal = "".join(
                str(part.value)
                for part in node.values
                if isinstance(part, ast.Constant)
            )
            if "/" not in literal:
                continue
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    text = ast.unparse(part.value)
                    if text not in allowed and not text.startswith("segment("):
                        raw.append(f"{path.name}:{node.lineno}: {text}")
    assert raw == []
