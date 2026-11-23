from unittest.mock import Mock

import pytest

from py_jama_client.apis.attachments_api import AttachmentsAPI
from py_jama_client.apis.projects_api import ProjectsAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    ResourceNotFoundException,
    UnauthorizedException,
)

MISSING_PROJECT_ID = 2147483647


@pytest.fixture(scope="function")
def projects_api(get_test_jama_client):
    api_instance = ProjectsAPI(get_test_jama_client)
    return api_instance


def test_get_projects(projects_api, bounded_pages):
    response = projects_api.get_projects()
    total_results = bounded_pages["offset_total"]
    assert response.data
    assert len(response.data) == min(12, total_results)
    assert all({"id", "type", "isFolder", "fields"} <= set(p) for p in response.data)
    assert {p["type"] for p in response.data} == {"projects"}
    assert all("name" in p["fields"] for p in response.data)
    assert all("projectKey" in p for p in response.data if not p["isFolder"])


def test_get_project_by_id(projects_api, real_project):
    response = projects_api.get_project_by_id(project_id=real_project)
    assert response.data["id"] == real_project
    assert response.data["type"] == "projects"
    assert response.data["fields"]["name"]


def test_get_item_types_in_project(projects_api, real_project, real_item_type):
    response = projects_api.get_item_types_in_project(project_id=real_project)
    assert all({"id", "typeKey", "display", "type"} <= set(t) for t in response.data)
    assert {t["type"] for t in response.data} == {"itemtypes"}
    assert real_item_type in {t["id"] for t in response.data}


def test_get_item_types_in_project_missing_project(projects_api):
    with pytest.raises(ResourceNotFoundException):
        projects_api.get_item_types_in_project(project_id=MISSING_PROJECT_ID)


def test_get_tags_in_project(projects_api, real_project, real_tag):
    response = projects_api.get_tags_in_project(project_id=real_project)
    assert all({"id", "name", "project"} <= set(t) for t in response.data)
    assert {t["project"] for t in response.data} == {real_project}
    assert real_tag in {t["id"] for t in response.data}


def test_get_tags_in_project_missing_project(projects_api):
    with pytest.raises(ResourceNotFoundException):
        projects_api.get_tags_in_project(project_id=MISSING_PROJECT_ID)


def test_post_project_docs(projects_api):
    # The docs give no example request body, only the RequestProject model.
    response = projects_api.post_project(
        {
            "projectKey": "EXMPL",
            "isFolder": False,
            "parent": 7,
            "fields": {"name": "Example project"},
        }
    )
    assert response.meta["status"] == "OK"
    assert response.data == {}


def test_put_project_docs(projects_api):
    # The docs give no example request body, only the RequestProject model.
    status = projects_api.put_project(
        5, {"fields": {"name": "Example project renamed"}}
    )
    assert status == 200


def test_delete_project_item_type_docs(projects_api):
    assert projects_api.delete_project_item_type(5, 6) == 204


def offline_admin_api():
    client = Mock()
    for verb in ("post", "put", "delete"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"meta": {}}), text=""
        )
    return ProjectsAPI(client), client


@pytest.mark.parametrize(
    ("call", "verb"),
    [
        (lambda api, params: api.post_project({}, params=params), "post"),
        (lambda api, params: api.put_project(5, {}, params=params), "put"),
    ],
    ids=["post", "put"],
)
def test_admin_writes_forward_params_untouched(call, verb):
    api, client = offline_admin_api()
    params = {"a": 1}
    call(api, params)
    assert getattr(client, verb).call_args.args[1] == {"a": 1}
    assert params == {"a": 1}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_project({}),
        lambda api: api.put_project(5, {}),
        lambda api: api.delete_project_item_type(5, 6),
    ],
    ids=["post", "put", "delete"],
)
def test_admin_writes_wrap_core_exception(call):
    api, client = offline_admin_api()
    for verb in ("post", "put", "delete"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_put_project_item_type_passes_caller_headers():
    api, client = offline_admin_api()
    caller = {"x-custom": "1"}
    api.put_project_item_type(5, 6, headers=caller)
    assert client.put.call_args.kwargs["headers"] == {
        "x-custom": "1",
        "content-type": "application/json",
    }
    assert caller == {"x-custom": "1"}
    api.put_project_item_type(5, 6)
    assert client.put.call_args.kwargs["headers"] == {
        "content-type": "application/json"
    }


def test_get_relationship_rule_set_projects_docs(projects_api):
    # The docs show relationship-shaped data for the rule set endpoints.
    response = projects_api.get_relationship_rule_set_projects(9)
    assert len(response.data) == 2
    assert response.meta["pageInfo"]["totalResults"] == 2


SCRATCH_TEXT = b"Scratch attachment for API tests.\n"


def test_post_project_attachment(
    projects_api, get_test_jama_client, real_project, resolved, tmp_path
):
    # Creates MockAttachment<N>, which the API cannot delete.
    name = resolved("scratch_attachment_name")
    attachments_api = AttachmentsAPI(get_test_jama_client)
    response = projects_api.post_project_attachment(
        real_project, name, "Scratch attachment for API tests."
    )
    assert response.meta["status"] == "Created"
    attachment_id = response.meta["id"]
    upload = tmp_path / f"{name}.txt"
    upload.write_bytes(SCRATCH_TEXT)
    assert attachments_api.put_attachments_file(attachment_id, str(upload)) == 200

    attachment = attachments_api.get_attachment(attachment_id).data
    assert attachment["project"] == real_project
    assert attachment["fields"]["name"] == name
    assert attachment["fileName"] == f"{name}.txt"
    assert attachment["fileSize"] == len(SCRATCH_TEXT)
    assert attachments_api.get_attachment_file(attachment_id) == SCRATCH_TEXT


def test_put_project_item_type_docs(projects_api):
    assert projects_api.put_project_item_type(5, 6) == 200


def test_get_project_by_id_core_exception_is_not_found():
    api, client = offline_admin_api()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(ResourceNotFoundException):
        api.get_project_by_id(5)


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.post_project_attachment(5, "n", "d"),
        lambda api: api.put_project_item_type(5, 6),
    ],
    ids=["post_project_attachment", "put_project_item_type"],
)
def test_attachment_and_item_type_writes_wrap_core_exception(call):
    api, client = offline_admin_api()
    client.post.side_effect = CoreException("boom")
    client.put.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_get_relationship_rule_set_projects_without_permission(projects_api):
    with pytest.raises(UnauthorizedException):
        projects_api.get_relationship_rule_set_projects(9)


def test_put_project_item_type_caller_header_overrides_case_insensitively():
    client = Mock()
    client.put.return_value.status_code = 200
    ProjectsAPI(client).put_project_item_type(
        5, 6, headers={"Content-Type": "application/xml", "x-custom": "1"}
    )
    headers = client.put.call_args.kwargs["headers"]
    assert headers.get_list("content-type") == ["application/xml"]
    assert headers["x-custom"] == "1"
