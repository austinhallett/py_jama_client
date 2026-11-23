import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jama_cassette import (
    ReplayTransport,
    SwitchTransport,
    cassette_path,
    harness_client,
    load_cassette,
)

from py_jama_client.apis.items_api import ItemsAPI
from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.apis.test_plans_api import TestPlansAPI
from py_jama_client.exceptions import ResourceNotFoundException
from py_jama_client.response import ClientResponse

CASSETTES = Path(__file__).parent / "cassettes"
MANIFEST_NAME = "_fixtures.json"
TRANSPORT_PLUGIN = "jama_transport"


def pytest_addoption(parser):
    parser.getgroup("jama").addoption(
        "--jama-cassette-dir",
        default=str(CASSETTES),
        help="where cassettes are read",
    )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


def _read_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise TypeError("manifest is not a JSON object")
    return manifest


def _plugin(config):
    """Tests replay their cassettes unless a plugin registered as
    `jama_transport` provides the client, each test's transport and fixture
    values; it is told when each test finishes."""
    return config.pluginmanager.get_plugin(TRANSPORT_PLUGIN)


@pytest.fixture(scope="session")
def jama_switch():
    switch = SwitchTransport()
    yield switch
    switch.close()


@pytest.fixture(scope="session")
def resolved(request):
    """resolved(name): a fixture value such as a project id, from the manifest
    (`_fixtures.json` in the cassette dir)."""
    manifest_path = (
        Path(request.config.getoption("--jama-cassette-dir")) / MANIFEST_NAME
    )
    manifest = _read_manifest(manifest_path)
    plugin = _plugin(request.config)

    def resolve(name: str):
        if plugin:
            return plugin.resolve(name, manifest.get(name))
        if name not in manifest:
            pytest.fail(f"{name} missing from {manifest_path}")
        return manifest[name]

    return resolve


@pytest.fixture(autouse=True)
def jama_cassette(request):
    """Replay the HTTP traffic of every test that uses the Jama client,
    including its fixtures' setup and teardown."""
    if "get_test_jama_client" not in request.fixturenames:
        yield
        return
    switch = request.getfixturevalue("jama_switch")
    node = request.node
    callspec = getattr(node, "callspec", None)
    path = cassette_path(
        Path(request.config.getoption("--jama-cassette-dir")),
        request.path.stem,
        getattr(node, "originalname", node.name),
        callspec.id if callspec else None,
    )
    plugin = _plugin(request.config)
    if plugin:
        transport = plugin.transport(node, path)
    else:
        if not path.exists():
            pytest.fail(f"missing cassette {path}")
        transport = ReplayTransport(load_cassette(path)["interactions"])
        request.getfixturevalue("monkeypatch").setattr(
            "py_jama_client.client.time.sleep", lambda seconds: None
        )
    switch.current = transport
    try:
        yield
    finally:
        switch.current = None
    call, setup = getattr(node, "rep_call", None), getattr(node, "rep_setup", None)
    if call is not None and not call.failed:
        skipped = call.skipped
    elif call is None and setup is not None and setup.skipped:
        skipped = True
    else:
        return
    if plugin:
        plugin.finished(node, path, transport, skipped)
    else:
        transport.assert_all_used()


@pytest.fixture(scope="session")
def get_test_jama_client(request, jama_switch):
    plugin = _plugin(request.config)
    client = plugin.client(jama_switch) if plugin else harness_client(jama_switch)
    yield client
    client.close()


@pytest.fixture(scope="function")
def bounded_pages(monkeypatch, get_test_jama_client):
    page_size = 5
    page_sizes = {
        "result_limit": 12,
        "offset": [],
        "last_id": [],
        "offset_total": None,
        "last_id_total": None,
    }
    offset_remaining = [page_sizes["result_limit"]]
    last_id_remaining = {}
    client = get_test_jama_client
    get_all = client.get_all
    get_page = client.get_page
    get_all_lastid = RelationshipsAPI.get_all_lastid
    get_page_lastid = RelationshipsAPI.get_page_lastid

    def bounded_get_all(
        resource,
        params=None,
        allowed_results_per_page=50,
        **kwargs,
    ):
        return get_all(
            resource,
            params=params,
            allowed_results_per_page=page_size,
            **kwargs,
        )

    def bounded_get_all_lastid(
        api,
        resource_path,
        params=None,
        allowed_results_per_page=50,
        **kwargs,
    ):
        if api.client is not client:
            return get_all_lastid(
                api,
                resource_path,
                params=params,
                allowed_results_per_page=allowed_results_per_page,
                **kwargs,
            )
        return get_all_lastid(
            api,
            resource_path,
            params=params,
            allowed_results_per_page=page_size,
            **kwargs,
        )

    def limit_page(page, remaining):
        page.data = page.data[:remaining]
        return remaining - len(page.data)

    def get_limited_page(
        resource,
        start_at,
        params=None,
        allowed_results_per_page=50,
        **kwargs,
    ):
        if start_at == 0:
            offset_remaining[0] = page_sizes["result_limit"]
        page = get_page(
            resource,
            start_at,
            params=params,
            allowed_results_per_page=page_size,
            **kwargs,
        )
        if start_at == 0:
            page_sizes["offset_total"] = (page.meta.get("pageInfo") or {}).get(
                "totalResults"
            )
        offset_remaining[0] = limit_page(page, offset_remaining[0])
        page_sizes["offset"].append(len(page.data))
        if len(page.data) < page_size:
            page_info = page.meta.setdefault("pageInfo", {})
            page_info["startIndex"] = start_at
            page_info["totalResults"] = start_at + len(page.data)
        return page

    def get_limited_page_lastid(
        api,
        resource_path,
        last_id,
        params=None,
        allowed_results_per_page=50,
        **kwargs,
    ):
        if api.client is not client:
            return get_page_lastid(
                api,
                resource_path,
                last_id,
                params=params,
                allowed_results_per_page=allowed_results_per_page,
                **kwargs,
            )

        api_key = id(api)
        if last_id == 0:
            last_id_remaining[api_key] = page_sizes["result_limit"]
        remaining = last_id_remaining.get(api_key, page_sizes["result_limit"])
        page = get_page_lastid(
            api,
            resource_path,
            last_id,
            params=params,
            allowed_results_per_page=page_size,
            **kwargs,
        )
        if last_id == 0:
            page_sizes["last_id_total"] = (page.meta.get("pageInfo") or {}).get(
                "totalResults"
            )
        last_id_remaining[api_key] = limit_page(page, remaining)
        page_sizes["last_id"].append(len(page.data))
        return page

    monkeypatch.setattr(client, "get_all", bounded_get_all)
    monkeypatch.setattr(client, "get_page", get_limited_page)
    monkeypatch.setattr(RelationshipsAPI, "get_all_lastid", bounded_get_all_lastid)
    monkeypatch.setattr(RelationshipsAPI, "get_page_lastid", get_limited_page_lastid)
    return page_sizes


@pytest.fixture(scope="session")
def get_example_client_response():
    return ClientResponse(
        meta={
            "status": "OK",
            "timestamp": "2024-01-24T14:19:40.043+0000",
            "pageInfo": {"startIndex": 0, "resultCount": 20, "totalResults": 515},
        },
        links={
            "data.itemType": {
                "type": "itemtypes",
                "href": ("https://jama.example.com/rest/v1/itemtypes/{data.itemType}"),
            },
            "data.location.parent.project": {
                "type": "projects",
                "href": (
                    "https://jama.example.com/rest/v1/projects/"
                    "{data.location.parent.project}"
                ),
            },
            "data.fields.status": {
                "type": "picklistoptions",
                "href": (
                    "https://jama.example.com/rest/v1/"
                    "picklistoptions/"
                    "{data.fields.status}"
                ),
            },
        },
        linked={"test": "linked"},
        data=[
            {
                "id": 50621,
                "documentKey": "PRJ-CMP-122",
                "globalId": "GID-81458",
                "itemType": 30,
                "project": 82,
                "createdDate": "2021-04-23T19:56:56.000+0000",
                "modifiedDate": "2021-04-23T19:56:56.000+0000",
                "lastActivityDate": "2021-04-28T19:46:40.000+0000",
                "createdBy": 1,
                "modifiedBy": 1,
                "fields": {
                    "documentKey": "PRJ-CMP-122",
                    "globalId": "GID-81458",
                    "name": "Security Requirments",
                    "description": "",
                },
                "resources": {"self": {"allowed": ["GET", "PUT", "PATCH", "DELETE"]}},
                "location": {
                    "sortOrder": 0,
                    "globalSortOrder": 4902930,
                    "sequence": "1",
                    "parent": {"project": 82},
                },
                "lock": {"locked": False},
                "type": "items",
            },
            {
                "id": 47639,
                "documentKey": "PRJ-SET-210",
                "globalId": "GID-80070",
                "itemType": 31,
                "project": 82,
                "createdDate": "2021-03-30T18:26:12.000+0000",
                "modifiedDate": "2021-03-30T18:26:12.000+0000",
                "lastActivityDate": "2021-04-23T19:57:03.000+0000",
                "createdBy": 1,
                "modifiedBy": 1,
                "fields": {
                    "setKey": "DOC",
                    "globalId": "GID-80070",
                    "documentKey": "PRJ-SET-210",
                    "name": "Documentation",
                    "description": "",
                },
                "resources": {"self": {"allowed": ["GET", "PUT", "PATCH", "DELETE"]}},
                "location": {
                    "sortOrder": 0,
                    "globalSortOrder": 9805860,
                    "sequence": "1.1",
                    "parent": {"item": 50621},
                },
                "lock": {"locked": False},
                "childItemType": 1,
                "type": "items",
            },
        ],
    )


@pytest.fixture(scope="session")
def real_abstract_item(resolved):
    return resolved("real_abstract_item")


@pytest.fixture(scope="session")
def real_attached_item(resolved):
    return resolved("real_attached_item")


@pytest.fixture(scope="session")
def real_abstract_item_version(resolved):
    return resolved("real_abstract_item_version")


@pytest.fixture(scope="session")
def real_baseline(resolved):
    return resolved("real_baseline")


@pytest.fixture(scope="session")
def real_baseline_versioned_item(resolved):
    return resolved("real_baseline_versioned_item")


@pytest.fixture(scope="session")
def real_project(resolved):
    return resolved("real_project")


@pytest.fixture(scope="session")
def real_item_type(resolved):
    return resolved("real_item_type")


@pytest.fixture(scope="session")
def real_relationship(resolved):
    return resolved("real_relationship")


@pytest.fixture(scope="session")
def real_relationship_type(resolved):
    return resolved("real_relationship_type")


@pytest.fixture(scope="session")
def real_tag(resolved):
    return resolved("real_tag")


@pytest.fixture(scope="session")
def real_release(resolved):
    return resolved("real_release")


@pytest.fixture(scope="session")
def real_attachment(resolved):
    return resolved("real_attachment")


@pytest.fixture(scope="session")
def real_scratch_attachment(resolved):
    return resolved("real_scratch_attachment")


@pytest.fixture(scope="session")
def real_filter(resolved):
    return resolved("real_filter")


@pytest.fixture(scope="session")
def current_user(resolved, get_test_jama_client):
    return resolved("current_user")


@pytest.fixture(scope="session")
def real_test_case(resolved):
    return resolved("real_test_case")


@pytest.fixture(scope="session")
def real_test_plan(resolved):
    return resolved("real_test_plan")


@pytest.fixture(scope="session")
def real_test_cycle(resolved):
    return resolved("real_test_cycle")


@pytest.fixture(scope="session")
def real_test_run(resolved):
    return resolved("real_test_run")


@pytest.fixture(scope="session")
def real_comment(resolved):
    return resolved("real_comment")


@pytest.fixture(scope="function")
def scratch_test_plan(request, get_test_jama_client, real_project):
    """A throwaway test plan, deleted on teardown even if the test failed or
    already deleted it."""
    test_plans_api = TestPlansAPI(get_test_jama_client)
    plan_id = test_plans_api.post_test_plan(
        real_project, {"name": f"zz-char-{request.node.name}"}
    ).meta["id"]
    try:
        yield plan_id
    finally:
        try:
            test_plans_api.delete_test_plan(plan_id)
        except ResourceNotFoundException:
            pass


@pytest.fixture(scope="function")
def scratch_item(
    request, get_test_jama_client, real_project, real_item_type, real_abstract_item
):
    """Factory for throwaway items under the fixture item or under another
    scratch item; every item it created or tracked is deleted on teardown
    (newest first, so children go before parents), even if the test failed."""
    items_api = ItemsAPI(get_test_jama_client)
    created = []
    status = 561

    def create(suffix="", parent=None):
        # 561 is MOCK's "Draft" option of the REQ status picklist.
        name = f"zz-char-{request.node.name}" + (f"-{suffix}" if suffix else "")
        location = {"item": real_abstract_item if parent is None else parent}
        item_id = items_api.post_item(
            real_project,
            real_item_type,
            real_item_type,
            location,
            {"name": name, "status": status},
        ).meta["id"]
        created.append(item_id)
        return item_id

    yield SimpleNamespace(create=create, track=created.append, status=status)
    failures = []
    for item_id in reversed(created):
        try:
            items_api.delete_item(item_id)
        except ResourceNotFoundException:
            pass
        except Exception as error:  # noqa: BLE001
            failures.append((item_id, str(error)))
    assert not failures, f"scratch items left behind: {failures}"
