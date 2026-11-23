"""Replay httpx traffic from JSON cassettes for offline tests."""

import base64
import datetime
import email.parser
import email.policy
import functools
import json
import re
from pathlib import Path

import httpx

from py_jama_client.client import JamaClient

CASSETTE_VERSION = 1
SOURCES = {"live", "docs", "synthetic"}
TOKEN_PATH = "/rest/oauth/token"
REPLAY_TOKEN = {"access_token": "replay", "expires_in": 3600, "token_type": "bearer"}
REPLAY_HOST = "https://jama.example.com"

CUSTOM_FIELD = re.compile(r"[A-Za-z_]\w*\$\d+")
STOCK_CONFIG_NAMES = {
    "Attachment",
    "Component",
    "Derived from",
    "Folder",
    "Related to",
    "Requirement",
    "Set",
    "Test Case",
    "Test Cycle",
    "Test Plan",
    "Test Run",
    "Text",
}

# Bodies are stored decoded, so headers describing the wire encoding no longer apply.
_WIRE_HEADERS = {"content-encoding", "content-length", "transfer-encoding"}


class CassetteMismatch(AssertionError):
    """A request did not match the next recorded interaction."""


def _media_type(content_type: str | None) -> str:
    return (content_type or "").split(";")[0].strip().lower()


def _encode_body(content: bytes | None, content_type: str | None) -> dict | None:
    if not content:
        return None
    if _media_type(content_type).endswith("json"):
        try:
            return {"json": json.loads(content)}
        except ValueError:
            pass
    try:
        return {"text": content.decode("utf-8")}
    except UnicodeDecodeError:
        return {"base64": base64.b64encode(content).decode("ascii")}


def _decode_body(body: dict | None) -> bytes:
    if body is None:
        return b""
    if "json" in body:
        return json.dumps(body["json"]).encode("utf-8")
    if "text" in body:
        return body["text"].encode("utf-8")
    return base64.b64decode(body["base64"])


def _multipart_parts(content: bytes, content_type: str) -> list[dict]:
    message = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(
        b"Content-Type: " + content_type.encode("latin-1") + b"\r\n\r\n" + content
    )
    parts = []
    for part in message.iter_parts():
        encoded: dict = {"name": part.get_param("name", header="content-disposition")}
        filename = part.get_filename()
        if filename is None:
            payload = part.get_payload(decode=True)
            encoded["value"] = _encode_body(
                payload if isinstance(payload, bytes) else None, None
            )
        else:
            encoded["filename"] = filename
        parts.append(encoded)
    return parts


def encode_request(request: httpx.Request) -> dict:
    """The matching key of a request: method, path, sorted query and body.

    Host and headers are ignored. Query pairs are sorted by name only, so
    repeated names keep their order. A multipart body is reduced to its media
    type, each part's name, and the filename of file parts or the value of
    other parts (the boundary is random).
    """
    content = request.read()
    content_type = request.headers.get("content-type")
    encoded = {
        "method": request.method,
        "path": request.url.path,
        "query": sorted(
            ([k, v] for k, v in request.url.params.multi_items()), key=lambda kv: kv[0]
        ),
    }
    if _media_type(content_type) == "multipart/form-data":
        encoded["body"] = {
            "multipart": {
                "content_type": "multipart/form-data",
                "parts": _multipart_parts(content, content_type),
            }
        }
    else:
        body = _encode_body(content, content_type)
        if body is not None:
            encoded["body"] = body
    return encoded


def encode_response(response: httpx.Response, content: bytes) -> dict:
    encoded = {
        "status": response.status_code,
        "headers": [
            [k, v] for k, v in response.headers.multi_items() if k not in _WIRE_HEADERS
        ],
    }
    body = _encode_body(content, response.headers.get("content-type"))
    if body is not None:
        encoded["body"] = body
    return encoded


def _canonical(value) -> str:
    """JSON text that tells `true` from `1` and `1` from `1.0`."""
    return json.dumps(value, sort_keys=True)


def _is_token_request(request: httpx.Request) -> bool:
    return request.method == "POST" and request.url.path.endswith(TOKEN_PATH)


class ReplayTransport(httpx.BaseTransport):
    """Answer requests from recorded interactions, strictly in order.

    The token request gets a canned token and consumes no interaction.
    Not thread-safe: one client, one thread.
    """

    def __init__(self, interactions: list[dict]):
        self.interactions = interactions
        self.position = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if _is_token_request(request):
            return httpx.Response(200, json=REPLAY_TOKEN, request=request)
        actual = drop_custom_fields(encode_request(request))
        if self.position >= len(self.interactions):
            raise CassetteMismatch(
                f"request {self.position + 1} has no recorded interaction: "
                f"{json.dumps(actual, sort_keys=True)}"
            )
        expected = self.interactions[self.position]["request"]
        if _canonical(actual) != _canonical(expected):
            raise CassetteMismatch(
                f"request {self.position + 1} does not match the cassette\n"
                f"expected: {json.dumps(expected, sort_keys=True)}\n"
                f"actual:   {json.dumps(actual, sort_keys=True)}"
            )
        recorded = self.interactions[self.position]["response"]
        self.position += 1
        return httpx.Response(
            recorded["status"],
            headers=recorded.get("headers", []),
            stream=httpx.ByteStream(_decode_body(recorded.get("body"))),
            request=request,
        )

    def assert_all_used(self) -> None:
        unused = self.interactions[self.position :]
        if unused:
            first = unused[0]["request"]
            raise CassetteMismatch(
                f"{len(unused)} recorded interaction(s) never requested; "
                f"next: {first['method']} {first['path']}"
            )


class SwitchTransport(httpx.BaseTransport):
    """Route requests to the active test's transport (`current`), else to
    `fallback`. With neither, answer the token request with
    a canned token and refuse everything else."""

    def __init__(self, fallback: httpx.BaseTransport | None = None):
        self.fallback = fallback
        self.current: httpx.BaseTransport | None = None

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if self.current is not None:
            return self.current.handle_request(request)
        if self.fallback is not None:
            return self.fallback.handle_request(request)
        if _is_token_request(request):
            return httpx.Response(200, json=REPLAY_TOKEN, request=request)
        raise CassetteMismatch(
            f"{request.method} {request.url.path} sent outside a test's cassette"
        )

    def close(self) -> None:
        if self.fallback is not None:
            self.fallback.close()


def cassette_path(root: Path, module: str, test: str, param_id: str | None) -> Path:
    """`<root>/<module>/<test>[<param id>].json`, with the parameter id made
    safe for file names."""
    name = test
    if param_id:
        name += "[" + re.sub(r"[^\w.-]+", "_", param_id) + "]"
    return root / module / f"{name}.json"


def save_cassette(path: Path, *args, **kwargs) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cassette_text(*args, **kwargs), encoding="utf-8")


def cassette_text(
    test: str,
    interactions: list[dict],
    *,
    source: str = "live",
    run_id: str,
    recorded: datetime.date | None = None,
) -> str:
    if source not in SOURCES:
        raise ValueError(f"unknown cassette source {source!r}")
    cassette = {
        "version": CASSETTE_VERSION,
        "test": test,
        "source": source,
        "recorded": (recorded or datetime.date.today()).isoformat(),
        "run_id": run_id,
        "interactions": interactions,
    }
    return json.dumps(cassette, indent=2) + "\n"


def load_cassette(path: Path) -> dict:
    cassette = json.loads(path.read_text(encoding="utf-8"))
    if cassette.get("version") != CASSETTE_VERSION:
        raise ValueError(
            f"{path}: cassette version {cassette.get('version')!r}, "
            f"expected {CASSETTE_VERSION}"
        )
    if cassette.get("source") not in SOURCES:
        raise ValueError(f"{path}: unknown cassette source {cassette.get('source')!r}")
    return cassette


def harness_client(
    transport: httpx.BaseTransport,
    host: str = REPLAY_HOST,
    credentials: tuple[str, str] = ("replay", "replay"),
    oauth: bool = True,
    **kwargs,
) -> JamaClient:
    """A JamaClient whose session sends every request through `transport`.

    httpx ignores `verify` when given a transport, so TLS settings belong on
    the inner transport (e.g. `httpx.HTTPTransport(verify=...)`).
    """

    class HarnessClient(JamaClient):
        session_class = staticmethod(
            functools.partial(httpx.Client, transport=transport)
        )

    return HarnessClient(host, credentials, oauth=oauth, **kwargs)


def drop_custom_fields(value):
    """Copy of `value` without custom fields: keys that contain a field name
    followed by `$` and digits (including `links` keys such as
    `data.fields.<name>$<digits>`), and list entries (field definitions)
    whose `name` is one."""
    if isinstance(value, dict):
        return {
            k: drop_custom_fields(v)
            for k, v in value.items()
            if not CUSTOM_FIELD.search(k)
        }
    if isinstance(value, list):
        return [
            drop_custom_fields(v)
            for v in value
            if not (
                isinstance(v, dict)
                and isinstance(v.get("name"), str)
                and CUSTOM_FIELD.search(v["name"])
            )
        ]
    return value


def _kept_string(key) -> bool:
    return isinstance(key, str) and (
        key in {"type", "globalId", "mimeType"} or key.endswith("Date")
    )


def _int(value) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def project_of(obj: dict) -> int | None:
    """The project an object belongs to: `project`, `location.project`, or
    the project of a nested child such as a version's `versionedItem`."""
    if _int(obj.get("project")) is not None:
        return obj["project"]
    location = obj.get("location")
    if isinstance(location, dict) and _int(location.get("project")) is not None:
        return location["project"]
    for child in obj.values():
        for candidate in child if isinstance(child, list) else [child]:
            if (
                isinstance(candidate, dict)
                and _int(candidate.get("project")) is not None
            ):
                return candidate["project"]
    return None


def is_transition(obj: dict) -> bool:
    return isinstance(obj.get("action"), str) and (
        "fromStatus" in obj or "toStatus" in obj
    )
