import base64
import gzip
import io
from pathlib import Path

import httpx
import pytest
from jama_cassette import (
    REPLAY_TOKEN,
    CassetteMismatch,
    ReplayTransport,
    SwitchTransport,
    cassette_path,
    encode_request,
    encode_response,
    harness_client,
    load_cassette,
    save_cassette,
)

from py_jama_client.client import JamaClient
from py_jama_client.exceptions import ResourceNotFoundException

BASE = "https://jama.invalid/rest/v1/"
TOKEN_URL = "https://jama.invalid/rest/oauth/token"


def fake_server(request):
    if request.url.path.endswith("/oauth/token"):
        return httpx.Response(200, json={"access_token": "real", "expires_in": 60})
    if request.url.path.endswith("/items/404"):
        return httpx.Response(
            404, json={"meta": {"status": "Not Found", "message": "nope"}}
        )
    if request.url.path.endswith("/gzipped"):
        return httpx.Response(
            200,
            headers={"content-type": "text/plain", "content-encoding": "gzip"},
            content=gzip.compress(b"unzipped"),
        )
    if request.url.path.endswith("/binary"):
        return httpx.Response(
            200,
            headers={"content-type": "application/octet-stream"},
            content=b"\xff\x00\xfe",
        )
    if request.url.path.endswith("/ordered"):
        return httpx.Response(
            200,
            headers=[("set-cookie", "a=1; Path=/"), ("set-cookie", "b=2")],
            content=b'{"z": 1, "a": 2}',
        )
    if request.method == "POST":
        return httpx.Response(201, json={"meta": {"id": 7}})
    return httpx.Response(200, json={"data": [{"id": 1}], "meta": {}})


def exchanges(calls):
    """Cassette interactions (and responses) for `calls` answered by
    fake_server; the token request is left out, as in a cassette."""
    interactions = []

    def handler(request):
        response = fake_server(request)
        content = response.read()
        encoded = encode_response(response, content)
        if not request.url.path.endswith("/oauth/token"):
            interactions.append(
                {"request": encode_request(request), "response": encoded}
            )
        return httpx.Response(
            response.status_code, headers=encoded["headers"], content=content
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        responses = [call(client) for call in calls]
    return interactions, responses


def replay_client(interactions):
    transport = ReplayTransport(interactions)
    return transport, httpx.Client(transport=transport)


def upload(client, filename, content=b"abc"):
    return client.put(
        BASE + "attachments/5/file", files={"file": (filename, io.BytesIO(content))}
    )


def test_exchanges_replay_in_order(tmp_path):
    calls = [
        lambda c: c.get(BASE + "items", params={"project": 1, "maxResults": 5}),
        lambda c: c.post(BASE + "items", json={"project": 1, "fields": {"name": "x"}}),
        lambda c: c.get(BASE + "items/404"),
    ]
    interactions, live = exchanges(calls)
    path = tmp_path / "cassettes" / "mod" / "test.json"
    save_cassette(path, "test/mod.py::test", interactions, run_id="r1")

    cassette = load_cassette(path)
    transport, client = replay_client(cassette["interactions"])
    with client:
        replayed = [call(client) for call in calls]
    transport.assert_all_used()

    assert [(r.status_code, r.json()) for r in replayed] == [
        (r.status_code, r.json()) for r in live
    ]
    assert cassette["test"] == "test/mod.py::test"
    assert cassette["source"] == "live"
    assert cassette["run_id"] == "r1"


def test_request_key_ignores_host_query_order_and_json_key_order():
    interactions, _ = exchanges(
        [lambda c: c.post(BASE + "items?b=2&a=1", json={"x": 1, "y": [1, 2]})]
    )
    transport, client = replay_client(interactions)
    with client:
        response = client.post(
            "https://other.invalid/rest/v1/items?a=1&b=2", json={"y": [1, 2], "x": 1}
        )
    transport.assert_all_used()
    assert response.status_code == 201
    assert interactions[0]["request"]["query"] == [["a", "1"], ["b", "2"]]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.put(BASE + "items", json={"x": 1}),
        lambda c: c.post(BASE + "relationships", json={"x": 1}),
        lambda c: c.post(BASE + "items?a=2", json={"x": 1}),
        lambda c: c.post(BASE + "items", json={"x": 2}),
        lambda c: c.post(BASE + "items"),
    ],
    ids=["method", "path", "query", "json-body", "missing-body"],
)
def test_mismatched_request_raises(call):
    interactions, _ = exchanges([lambda c: c.post(BASE + "items", json={"x": 1})])
    _, client = replay_client(interactions)
    with client, pytest.raises(CassetteMismatch, match="does not match"):
        call(client)


def test_request_beyond_cassette_raises():
    interactions, _ = exchanges([lambda c: c.get(BASE + "items")])
    _, client = replay_client(interactions)
    with client:
        client.get(BASE + "items")
        with pytest.raises(CassetteMismatch, match="no recorded interaction"):
            client.get(BASE + "items")


def test_unused_interactions_fail_the_check():
    interactions, _ = exchanges(
        [lambda c: c.get(BASE + "items"), lambda c: c.delete(BASE + "tags/3")]
    )
    transport, client = replay_client(interactions)
    with client:
        client.get(BASE + "items")
    with pytest.raises(CassetteMismatch, match="1 recorded interaction.*DELETE"):
        transport.assert_all_used()


def test_token_request_is_not_recorded_and_replays_canned_token():
    interactions, _ = exchanges(
        [
            lambda c: c.post(TOKEN_URL, data={"grant_type": "client_credentials"}),
            lambda c: c.get(BASE + "items"),
        ]
    )
    assert [i["request"]["path"] for i in interactions] == ["/rest/v1/items"]

    transport, client = replay_client(interactions)
    with client:
        token = client.post(TOKEN_URL, data={"grant_type": "client_credentials"})
        client.get(BASE + "items")
        client.post(TOKEN_URL, data={"grant_type": "client_credentials"})
    transport.assert_all_used()
    assert token.json() == REPLAY_TOKEN


def test_multipart_matches_on_part_names_and_filenames_not_boundary_or_bytes():
    interactions, _ = exchanges([lambda c: upload(c, "a.txt", b"first")])
    assert interactions[0]["request"]["body"] == {
        "multipart": {
            "content_type": "multipart/form-data",
            "parts": [{"name": "file", "filename": "a.txt"}],
        }
    }

    transport, client = replay_client(interactions)
    with client:
        assert upload(client, "a.txt", b"second").status_code == 200
    transport.assert_all_used()

    _, client = replay_client(interactions)
    with client, pytest.raises(CassetteMismatch):
        upload(client, "b.txt")


def test_recorded_404_raises_resource_not_found_on_replay():
    interactions, _ = exchanges([lambda c: c.get(BASE + "items/404")])
    _, client = replay_client(interactions)
    with client:
        response = client.get(BASE + "items/404")
    with pytest.raises(ResourceNotFoundException):
        JamaClient.handle_response_status(response)


def test_compressed_response_is_stored_decoded_and_replays():
    interactions, live = exchanges([lambda c: c.get(BASE + "gzipped")])
    assert live[0].text == "unzipped"
    recorded = interactions[0]["response"]
    assert recorded["body"] == {"text": "unzipped"}
    assert "content-encoding" not in recorded["headers"]
    assert "content-length" not in recorded["headers"]

    _, client = replay_client(interactions)
    with client:
        replayed = client.get(BASE + "gzipped")
        assert replayed.text == "unzipped"
        assert replayed.elapsed is not None


def test_binary_bodies_round_trip_as_base64():
    interactions, _ = exchanges([lambda c: c.put(BASE + "binary", content=b"\x80\x81")])
    assert interactions[0]["request"]["body"] == {"base64": "gIE="}
    assert interactions[0]["response"]["body"] == {"base64": "/wD+"}

    _, client = replay_client(interactions)
    with client:
        assert client.put(BASE + "binary", content=b"\x80\x81").content == (
            b"\xff\x00\xfe"
        )


def test_save_rejects_unknown_source(tmp_path):
    with pytest.raises(ValueError, match="source"):
        save_cassette(tmp_path / "c.json", "t", [], source="guess", run_id="r")


def test_load_rejects_other_versions(tmp_path):
    path = tmp_path / "c.json"
    save_cassette(path, "t", [], run_id="r")
    path.write_text(path.read_text().replace('"version": 1', '"version": 2'))
    with pytest.raises(ValueError, match="version"):
        load_cassette(path)


def test_replayed_json_keeps_server_key_order_and_repeated_headers(tmp_path):
    interactions, live = exchanges([lambda c: c.get(BASE + "ordered")])
    path = tmp_path / "c.json"
    save_cassette(path, "t", interactions, run_id="r")
    _, client = replay_client(load_cassette(path)["interactions"])
    with client:
        replayed = client.get(BASE + "ordered")
    assert list(replayed.json()) == list(live[0].json()) == ["z", "a"]
    assert replayed.headers.get_list("set-cookie") == ["a=1; Path=/", "b=2"]


def test_json_body_match_distinguishes_bool_int_and_float():
    interactions, _ = exchanges([lambda c: c.post(BASE + "items", json={"flag": True})])
    for other in (1, 1.0):
        _, client = replay_client(interactions)
        with client, pytest.raises(CassetteMismatch):
            client.post(BASE + "items", json={"flag": other})


def test_repeated_query_parameters_keep_their_order():
    interactions, _ = exchanges([lambda c: c.get(BASE + "items?sortBy=name&sortBy=id")])
    _, client = replay_client(interactions)
    with client, pytest.raises(CassetteMismatch):
        client.get(BASE + "items?sortBy=id&sortBy=name")


def test_multipart_form_field_values_must_match():
    def call(value):
        return lambda c: c.put(
            BASE + "attachments/5/file",
            files={"file": ("a.txt", io.BytesIO(b"x"))},
            data={"desc": value},
        )

    interactions, _ = exchanges([call("one")])
    _, client = replay_client(interactions)
    with client, pytest.raises(CassetteMismatch):
        call("two")(client)


def test_multipart_binary_form_field_is_matched_as_base64():
    def call(c):
        return c.put(
            BASE + "attachments/5/file",
            files={"file": ("a.txt", io.BytesIO(b"x")), "raw": (None, b"\xff")},
        )

    interactions, _ = exchanges([call])
    assert {"name": "raw", "value": {"base64": "/w=="}} in (
        interactions[0]["request"]["body"]["multipart"]["parts"]
    )
    transport, client = replay_client(interactions)
    with client:
        call(client)
    transport.assert_all_used()


def test_harness_client_passes_given_credentials_to_the_transport():
    seen = []

    def server(request):
        seen.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"data": {"id": 1}, "meta": {}})

    with harness_client(
        httpx.MockTransport(server),
        host="https://jama.invalid",
        credentials=("id", "secret"),
        oauth=False,
    ) as client:
        client.get("tags/1")

    assert seen == ["Basic " + base64.b64encode(b"id:secret").decode()]


def test_switch_routes_to_current_then_fallback():
    def server(name):
        return httpx.MockTransport(lambda request: httpx.Response(200, text=name))

    switch = SwitchTransport(fallback=server("fallback"))
    with httpx.Client(transport=switch) as client:
        assert client.get(BASE + "items").text == "fallback"
        switch.current = server("cassette")
        assert client.get(BASE + "items").text == "cassette"


def test_switch_without_fallback_only_answers_the_token_request():
    switch = SwitchTransport()
    with httpx.Client(transport=switch) as client:
        token = client.post(TOKEN_URL, data={"grant_type": "client_credentials"})
        assert token.json() == REPLAY_TOKEN
        with pytest.raises(CassetteMismatch, match="outside a test's cassette"):
            client.get(BASE + "items")


@pytest.mark.parametrize(
    "param_id, expected",
    [
        (None, "test_x.json"),
        ("a-1", "test_x[a-1].json"),
        ("a/b c", "test_x[a_b_c].json"),
        ("../up", "test_x[.._up].json"),
    ],
)
def test_cassette_path_is_one_file_per_test(param_id, expected):
    path = cassette_path(Path("root"), "test_mod", "test_x", param_id)
    assert path == Path("root", "test_mod", expected)
