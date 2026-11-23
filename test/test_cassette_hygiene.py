"""Fail if cassettes, the fixture manifest or test files could leak instance data."""

import base64
import binascii
import dataclasses
import json
import re
import sys
import urllib.parse
from pathlib import Path

import pytest
from jama_cassette import (
    STOCK_CONFIG_NAMES,
    _kept_string,
    is_transition,
    project_of,
)

TEST_DIR = Path(__file__).parent
MANIFEST = TEST_DIR / "cassettes" / "_fixtures.json"
SCANNED = sorted(
    p
    for p in TEST_DIR.rglob("*")
    if p.is_file()
    and "__pycache__" not in p.parts
    and not p.name.startswith(".")
    and p != Path(__file__)
    and p.suffix != ".pyc"
)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]*[A-Za-z]")
CUSTOM_FIELD = re.compile(r"[A-Za-z_]\w*\$\d+")
URL_HOST = re.compile(r"https?://([^/\s\"'<>:]+)")
GENERIC_CONFIG_NAME = re.compile(
    r"^(Item Types?|Pick List|Option|Relationship Type|Rule Set|Group) \d+$"
)
CONFIG_NAME_KEYS = {
    "itemtypes": "display",
    "picklists": "name",
    "picklistoptions": "name",
    "relationshiptypes": "name",
    "relationshiprulesets": "name",
    "usergroups": "name",
}
USER_NAME_KEYS = ("username", "firstName", "lastName", "email", "phone")


def _allowed_host(host: str) -> bool:
    host = host.lower()
    return host in {"localhost", "example.com"} or host.endswith(
        (".example.com", ".invalid")
    )


def _ints(value) -> set[int]:
    if isinstance(value, bool):
        return set()
    if isinstance(value, int):
        return {value}
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return set().union(*(_ints(v) for v in value)) if value else set()
    return set()


@dataclasses.dataclass(frozen=True)
class Keep:
    """Manifest objects allowed to keep their names, by kind. A manifest
    entry counts for a kind when its key names that kind (`real_project`)."""

    projects: frozenset[int] = frozenset()
    attachments: frozenset[int] = frozenset()
    filters: frozenset[int] = frozenset()
    releases: frozenset[int] = frozenset()

    def ids(self, kind: str) -> frozenset[int]:
        return getattr(self, kind, frozenset())


def manifest_keep() -> Keep:
    if not MANIFEST.exists():
        return Keep()
    return keep_from(json.loads(MANIFEST.read_text(encoding="utf-8")))


def keep_from(manifest: dict) -> Keep:
    return Keep(
        **{
            kind: frozenset(
                set().union(*(_ints(v) for k, v in manifest.items() if kind[:-1] in k))
            )
            for kind in ("projects", "attachments", "filters", "releases")
        }
    )


def text_leaks(text: str) -> list[str]:
    text = text + "\n" + urllib.parse.unquote(text)
    leaks = sorted({f"email {m}" for m in EMAIL.findall(text)})
    leaks += sorted({f"custom field {m}" for m in CUSTOM_FIELD.findall(text)})
    leaks += sorted(
        {f"host {h}" for h in URL_HOST.findall(text) if not _allowed_host(h)}
    )
    lowered = text.lower()
    if "jamacloud" in lowered:
        leaks.append("jamacloud host")
    if "Bearer " in text:
        leaks.append("Bearer token")
    return leaks


def _generic(value, pattern: str) -> bool:
    return value in (None, "") or re.fullmatch(pattern, value) is not None


def _strings_left(value, top=()) -> bool:
    """Whether a non-empty string remains, ignoring `top` keys at this level,
    dates/types anywhere, and nested objects placed in a project of their own."""
    items = value.items() if isinstance(value, dict) else enumerate(value)
    for key, item in items:
        if key in top:
            continue
        if isinstance(item, str):
            if item and not _kept_string(key):
                return True
        elif (
            isinstance(item, list)
            or (
                isinstance(item, dict)
                and not ("id" in item and "type" in item and project_of(item))
            )
        ) and _strings_left(item):
            return True
    return False


def _empty(obj: dict, keys) -> bool:
    return all(obj.get(k) in (None, "", [], {}) for k in keys)


def _kind_leaks(obj: dict, kind: str, object_id: int, keep: Keep) -> bool:
    """Whether an object of a generalized kind still holds identifying data."""
    fields = obj["fields"] if isinstance(obj.get("fields"), dict) else {}
    if kind == "users":
        return not (
            all(obj.get(k) in (None, f"user{object_id}") for k in USER_NAME_KEYS)
            and _empty(obj, ("title", "location", "uid", "avatarUrl", "customData"))
        )
    if kind == "usergroups":
        return not _empty(obj, ("description",))
    if kind in CONFIG_NAME_KEYS:
        return not _empty(obj, ("description", "value"))
    if object_id in keep.ids(kind):
        return False
    if kind == "projects":
        key = rf"PRJ{object_id}"
        return not (
            _generic(fields.get("name"), rf"Project {object_id}")
            and _generic(fields.get("projectKey"), key)
            and _generic(obj.get("projectKey"), key)
            and not _strings_left(fields, top={"name", "projectKey"})
        )
    if kind == "filters":
        return not (
            _generic(obj.get("name"), rf"Filter {object_id}")
            and not obj.get("filterQuery")
        )
    if kind == "releases":
        return not (
            _generic(obj.get("name"), rf"Release {object_id}")
            and _empty(obj, ("description",))
        )
    if kind == "attachments":
        project = project_of(obj)
        if project in keep.projects:
            return False
        document_key = rf"PRJ{project}-{object_id}" if project is not None else ".*"
        return not (
            _generic(fields.get("name"), rf"Attachment {object_id}")
            and _generic(obj.get("fileName"), rf"attachment{object_id}")
            and _generic(obj.get("documentKey"), document_key)
            and _generic(fields.get("documentKey"), document_key)
            and not _strings_left(fields, top={"name", "documentKey"})
        )
    return False


def _object_leaks(obj: dict, keep: Keep, structural: bool) -> list[str]:
    leaks = []
    token = obj.get("access_token")
    if token is not None and token != "replay":
        leaks.append("non-replay access_token")
    if not structural:
        return leaks
    if isinstance(obj.get("userName"), str) and not re.fullmatch(
        r"user\d*", obj["userName"]
    ):
        leaks.append("userName not generalized")
    if is_transition(obj) and not obj["action"].startswith("Transition "):
        leaks.append("workflow transition action not generalized")
    object_id, kind = obj.get("id"), obj.get("type")
    if not (isinstance(object_id, int) and isinstance(kind, str)):
        return leaks
    name_key = CONFIG_NAME_KEYS.get(kind)
    name = obj.get(name_key) if name_key else None
    if isinstance(name, str) and not (
        name in STOCK_CONFIG_NAMES or GENERIC_CONFIG_NAME.match(name)
    ):
        leaks.append(f"{kind} name not generalized (id {object_id})")
    if kind in {
        "users",
        "usergroups",
        "projects",
        "filters",
        "attachments",
        "releases",
    } or (name_key):
        if _kind_leaks(obj, kind, object_id, keep):
            leaks.append(f"{kind} {object_id} not generalized")
        return leaks
    project = project_of(obj)
    if project is None or project in keep.projects:
        return leaks
    label = rf"{kind} {object_id}"
    fields = obj["fields"] if isinstance(obj.get("fields"), dict) else {}
    top = {"name", "documentKey", "fields"}
    document_key = rf"PRJ{project}-{object_id}"
    if not (
        _generic(fields.get("name"), label)
        and _generic(obj.get("name"), label)
        and _generic(obj.get("documentKey"), document_key)
        and _generic(fields.get("documentKey"), document_key)
        and not _strings_left(obj, top=top)
        and not _strings_left(fields, top=top)
    ):
        leaks.append(f"{kind} {object_id} not generalized")
    return leaks


def document_leaks(value, keep: Keep = Keep(), structural=True) -> list[str]:
    leaks = []
    if isinstance(value, list):
        for v in value:
            leaks += document_leaks(v, keep, structural)
    elif isinstance(value, dict):
        leaks += _object_leaks(value, keep, structural)
        for v in value.values():
            leaks += document_leaks(v, keep, structural)
    return leaks


def _base64_bodies(value):
    if isinstance(value, list):
        for v in value:
            yield from _base64_bodies(v)
    elif isinstance(value, dict):
        if isinstance(value.get("base64"), str):
            try:
                yield base64.b64decode(value["base64"], validate=True).decode("latin-1")
            except binascii.Error:
                yield None
        for v in value.values():
            yield from _base64_bodies(v)


def file_leaks(path: Path, keep: Keep = Keep()) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["binary file cannot be scanned"]
    return content_leaks(text, keep, is_json=path.suffix == ".json")


def content_leaks(text: str, keep: Keep = Keep(), is_json: bool = True) -> list[str]:
    leaks = text_leaks(text)
    if is_json:
        document = json.loads(text)
        hand_written = isinstance(document, dict) and document.get("source") in {
            "docs",
            "synthetic",
        }
        leaks += document_leaks(document, keep, structural=not hand_written)
        for decoded in _base64_bodies(document):
            if decoded is None:
                leaks.append("invalid base64 body")
            else:
                leaks += [f"in base64 body: {leak}" for leak in text_leaks(decoded)]
    return leaks


@pytest.mark.parametrize("path", SCANNED, ids=lambda p: str(p.relative_to(TEST_DIR)))
def test_no_instance_data(path):
    assert file_leaks(path, manifest_keep()) == []


@pytest.mark.parametrize(
    "planted, expected",
    [
        ("contact " + "someone" + "@" + "corp.test", "email"),
        ('{"fields": {"import_id' + '$24": 1}}', "custom field"),
        ("see https://" + "jama.corp.test/rest/v1/items", "host"),
        ("see https%3A%2F%2F" + "jama.corp.test%2Fx", "host"),
        ("https://" + "acme." + "jamacloud.com", "jamacloud"),
        ("Authorization: " + "Bearer abc", "Bearer"),
    ],
)
def test_planted_text_leaks_are_found(planted, expected):
    assert any(expected in leak for leak in text_leaks(planted))


def test_planted_document_leaks_are_found():
    document = {
        "data": [
            {"id": 5, "type": "itemtypes", "display": "Special Variant"},
            {"id": 6, "type": "relationshiptypes", "name": "Relationship Type 6"},
            {"id": 7, "type": "itemtypes", "display": "Folder"},
            {"id": 8, "type": "users", "username": "jdoe"},
            {"id": 9, "type": "users", "username": "user9"},
            {"id": 2, "type": "projects", "fields": {"name": "Secret"}},
            {"id": 1, "type": "projects", "fields": {"name": "Sample_Things"}},
            {"id": 3, "type": "filters", "name": "Ours"},
            {"id": 4, "type": "attachments", "fields": {"name": "Plan"}},
            {"id": 10, "type": "items", "project": 2, "fields": {"name": "Secret"}},
            {"id": 11, "type": "items", "project": 1, "fields": {"name": "Widget"}},
            {"id": 12, "type": "items", "project": 2, "fields": {"name": "items 12"}},
        ],
        "token": {"access_token": "live-token"},
    }
    assert document_leaks(document, keep=Keep(projects=frozenset({1}))) == [
        "itemtypes name not generalized (id 5)",
        "users 8 not generalized",
        "projects 2 not generalized",
        "filters 3 not generalized",
        "attachments 4 not generalized",
        "items 10 not generalized",
        "non-replay access_token",
    ]


def _write(tmp_path, document) -> Path:
    path = tmp_path / "c.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_hand_written_cassettes_skip_structural_checks_only(tmp_path):
    data = {"id": 5, "type": "picklistoptions", "name": "High"}
    for source in ("docs", "synthetic"):
        assert file_leaks(_write(tmp_path, {"source": source, "data": data})) == []
    assert file_leaks(_write(tmp_path, {"source": "live", "data": data})) == [
        "picklistoptions name not generalized (id 5)"
    ]
    leaky = {"source": "docs", "data": {"name": "a" + "@" + "corp.test"}}
    assert file_leaks(_write(tmp_path, leaky)) == ["email a@corp.test"]


def test_base64_bodies_are_decoded_and_scanned(tmp_path):
    secret = base64.b64encode(("x " + "a" + "@" + "corp.test").encode()).decode()
    path = _write(tmp_path, {"source": "live", "body": {"base64": secret}})
    assert any(leak.startswith("in base64 body: email") for leak in file_leaks(path))


def test_binary_files_are_reported(tmp_path):
    path = tmp_path / "blob.bin"
    path.write_bytes(b"\xff\xfe\x00")
    assert file_leaks(path) == ["binary file cannot be scanned"]


def test_scan_covers_all_test_files():
    names = {str(p.relative_to(TEST_DIR)) for p in SCANNED}
    assert "conftest.py" in names
    assert any(n.startswith("cassettes/") for n in names)
    assert "test_cassette_hygiene.py" not in names


def test_manifest_keep_sets_are_per_kind(tmp_path, monkeypatch):
    manifest = tmp_path / "_fixtures.json"
    manifest.write_text(
        json.dumps(
            {
                "real_project": 1,
                "real_attachment": {"id": 2, "versions": [3, True]},
                "real_filter": 4,
                "real_item_type": 31,
            }
        )
    )
    monkeypatch.setattr(sys.modules[__name__], "MANIFEST", manifest)
    assert manifest_keep() == Keep(
        projects=frozenset({1}),
        attachments=frozenset({2, 3}),
        filters=frozenset({4}),
    )


def test_unrelated_manifest_ids_do_not_exempt_projects():
    keep = Keep(projects=frozenset({1}))
    project_31 = {"id": 31, "type": "projects", "fields": {"name": "Secret"}}
    assert document_leaks(project_31, keep) == ["projects 31 not generalized"]


def test_foreign_objects_must_be_fully_generalized():
    keep = Keep(projects=frozenset({1}))
    step_left = {
        "id": 6,
        "type": "items",
        "project": 2,
        "fields": {"name": "items 6", "steps": [{"action": "press it"}]},
    }
    comment = {
        "id": 7,
        "type": "comments",
        "location": {"item": 6, "project": 2},
        "body": {"text": "ship it"},
    }
    group = {"id": 8, "type": "usergroups", "name": "Our Team"}
    clean = {
        "id": 9,
        "type": "items",
        "project": 2,
        "globalId": "GID-9",
        "createdDate": "2026-01-01",
        "fields": {"name": "items 9", "documentKey": "PRJ2-9", "description": ""},
    }
    assert document_leaks([step_left, comment, group, clean], keep) == [
        "items 6 not generalized",
        "comments 7 not generalized",
        "usergroups name not generalized (id 8)",
    ]


def test_invalid_base64_is_reported(tmp_path):
    path = _write(tmp_path, {"source": "live", "body": {"base64": "not base64!"}})
    assert file_leaks(path) == ["invalid base64 body"]


def test_dotfiles_are_not_scanned():
    assert not any(p.name.startswith(".") for p in SCANNED)


def test_leftover_identifying_values_are_found():
    keep = Keep(projects=frozenset({1}))
    documents = [
        {
            "id": 2,
            "type": "projects",
            "fields": {"name": "Project 2", "description": "x"},
        },
        {"id": 3, "type": "filters", "name": "Filter 3", "filterQuery": {"v": ["x"]}},
        {"id": 4, "type": "picklists", "name": "Pick List 4", "description": "x"},
        {"id": 5, "type": "attachments", "fileName": "plan.pdf", "fields": {}},
        {"id": 6, "type": "users", "username": "user6", "title": "Boss"},
        {"id": 7, "type": "usergroups", "name": "Group 7", "description": "x"},
        {"type": "version", "userName": "Jane Doe"},
        {"id": "1-2", "action": "Send to Board", "fromStatus": 1, "toStatus": 2},
        {
            "id": 8,
            "type": "items",
            "project": 2,
            "fields": {"name": "items 8", "s": [{"name": "x"}]},
        },
    ]
    assert document_leaks(documents, keep) == [
        "projects 2 not generalized",
        "filters 3 not generalized",
        "picklists 4 not generalized",
        "attachments 5 not generalized",
        "users 6 not generalized",
        "usergroups 7 not generalized",
        "userName not generalized",
        "workflow transition action not generalized",
        "items 8 not generalized",
    ]


def test_foreign_document_keys_must_be_generalized():
    keep = Keep(projects=frozenset({1}))
    item = {
        "id": 6,
        "type": "items",
        "project": 2,
        "documentKey": "SECRET-REQ-6",
        "fields": {"name": "items 6", "documentKey": "SECRET-REQ-6"},
    }
    attachment = {
        "id": 7,
        "type": "attachments",
        "project": 2,
        "documentKey": "SECRET-ATT-7",
    }
    kept_attachment = {
        "id": 8,
        "type": "attachments",
        "project": 1,
        "fileName": "spec.txt",
    }
    assert document_leaks([item, attachment, kept_attachment], keep) == [
        "items 6 not generalized",
        "attachments 7 not generalized",
    ]


def test_unplaced_references_inside_foreign_objects_must_be_blank():
    keep = Keep(projects=frozenset({1}))
    item = {
        "id": 6,
        "type": "items",
        "project": 2,
        "fields": {"name": "", "ref": {"id": 5, "type": "items", "name": "Secret ref"}},
    }
    assert document_leaks(item, keep) == ["items 6 not generalized"]


def test_releases_outside_the_manifest_must_be_generalized():
    keep = Keep(releases=frozenset({1}))
    releases = [
        {"id": 1, "type": "releases", "project": 2, "name": "Ours", "description": "x"},
        {"id": 2, "type": "releases", "project": 2, "name": "Big Launch"},
        {
            "id": 3,
            "type": "releases",
            "project": 2,
            "name": "Release 3",
            "description": "y",
        },
        {
            "id": 4,
            "type": "releases",
            "project": 2,
            "name": "Release 4",
            "description": "",
        },
    ]
    assert document_leaks(releases, keep) == [
        "releases 2 not generalized",
        "releases 3 not generalized",
    ]
