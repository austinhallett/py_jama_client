import os
import ssl

import pytest

from py_jama_client.apis.abstract_items_api import AbstractItemsAPI
from py_jama_client.apis.baselines_api import BaselinesAPI
from py_jama_client.apis.item_types_api import ItemTypesAPI
from py_jama_client.apis.projects_api import ProjectsAPI
from py_jama_client.apis.relationships_api import RelationshipsAPI
from py_jama_client.apis.tags_api import TagsAPI
from py_jama_client.apis.users_api import UsersAPI
from py_jama_client.client import JamaClient
from py_jama_client.response import ClientResponse


@pytest.fixture(autouse=True, scope="session")
def connection_env_vars():
    needed_evs = ["CLIENT_ID", "CLIENT_SECRET", "HOST"]
    missing_evs = [ev for ev in needed_evs if ev not in os.environ]
    if len(missing_evs) > 0:
        bulleted_ev_list = "    - " + "\n                    - ".join(missing_evs)
        if len(missing_evs) > 1:
            singular_or_plural = "s"
        else:
            singular_or_plural = ""
        raise ValueError(
            f"""
                Please set the following environment variable{singular_or_plural}
                to run tests properly:
                {bulleted_ev_list}
            """
        )


@pytest.fixture(scope="session")
def get_test_jama_client():
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    client = JamaClient(
        host=os.getenv("HOST"),
        credentials=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")),
        verify=ssl_context,
        oauth=False,
    )

    yield client


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
                "href": (
                    "https://silabs.jamacloud.com/rest/v1/itemtypes/{data.itemType}"
                ),
            },
            "data.location.parent.project": {
                "type": "projects",
                "href": (
                    "https://silabs.jamacloud.com/rest/v1/projects/"
                    "{data.location.parent.project}"
                ),
            },
            "data.fields.verification_method$141": {
                "type": "picklistoptions",
                "href": (
                    "https://silabs.jamacloud.com/rest/v1/"
                    "picklistoptions/"
                    "{data.fields.verification_method$141}"
                ),
            },
        },
        linked={"test": "linked"},
        data=[
            {
                "id": 50621,
                "documentKey": "SYSSEC-CMP-122",
                "globalId": "GID-81458",
                "itemType": 30,
                "project": 82,
                "createdDate": "2021-04-23T19:56:56.000+0000",
                "modifiedDate": "2021-04-23T19:56:56.000+0000",
                "lastActivityDate": "2021-04-28T19:46:40.000+0000",
                "createdBy": 1,
                "modifiedBy": 1,
                "fields": {
                    "documentKey": "SYSSEC-CMP-122",
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
                "documentKey": "SYSSEC-SET-210",
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
                    "documentKey": "SYSSEC-SET-210",
                    "name": "Documentation",
                    "description": "",
                    "document_status$31": 566,
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
def real_abstract_item(get_test_jama_client, real_project, real_item_type):
    if "ABSTRACT_ITEM_ID" in os.environ:
        return os.environ.get("ABSTRACT_ITEM_ID")
    abstract_items_api = AbstractItemsAPI(get_test_jama_client)
    abstract_items = abstract_items_api.get_abstract_items(
        project=(real_project,), item_type=(real_item_type,)
    ).data
    if abstract_items == []:
        raise ValueError(
            """
                Unable to identify a viable abstract item for sample testing
            """
        )
    else:
        return abstract_items[0]["id"]


@pytest.fixture(scope="session")
def real_abstract_item_version(get_test_jama_client, real_abstract_item):
    if "ABSTRACT_ITEM_VERSION" in os.environ:
        return os.environ.get("ABSTRACT_ITEM_VERSION")
    abstract_items_api = AbstractItemsAPI(get_test_jama_client)
    abstract_item_versions = abstract_items_api.get_abstract_item_versions(
        item_id=real_abstract_item
    ).data
    if abstract_item_versions == []:
        raise ValueError(
            """
                Unable to identify a viable abstract item for sample
                version testing
            """
        )
    else:
        return abstract_item_versions[0]["versionNumber"]


@pytest.fixture(scope="session")
def real_baseline(get_test_jama_client, real_project):
    if "BASELINE_ID" in os.environ:
        return os.environ.get("BASELINE_ID")
    baselines_api = BaselinesAPI(get_test_jama_client)
    baselines = baselines_api.get_baselines(project_id=real_project).data
    if baselines == []:
        raise ValueError(
            """
                Unable to identify a viable baseline for sample testing
            """
        )
    else:
        return baselines[0]["id"]


@pytest.fixture(scope="session")
def real_baseline_versioned_item(get_test_jama_client, real_baseline):
    if "BASELINE_ID" in os.environ:
        return os.environ.get("BASELINE_ID")
    baselines_api = BaselinesAPI(get_test_jama_client)
    baseline_versioned_items = baselines_api.get_baseline_versioned_items(
        baseline_id=real_baseline
    ).data
    if baseline_versioned_items == []:
        raise ValueError(
            """
                Unable to identify a viable baseline for sample testing
            """
        )
    else:
        return baseline_versioned_items[0]["id"]


@pytest.fixture(scope="session")
def real_project(get_test_jama_client):
    if "PROJECT_ID" in os.environ:
        return os.environ.get("PROJECT_ID")
    projects_api = ProjectsAPI(get_test_jama_client)
    projects = projects_api.get_projects().data
    if projects == []:
        raise ValueError(
            """
                Unable to identify a viable project for sample testing
            """
        )
    else:
        # return 350
        return projects[0]["id"]


@pytest.fixture(scope="session")
def real_item_type(get_test_jama_client):
    if "ITEM_TYPE_ID" in os.environ:
        return os.environ.get("ITEM_TYPE_ID")
    item_types_api = ItemTypesAPI(get_test_jama_client)
    item_types = item_types_api.get_item_types().data
    if item_types == []:
        raise ValueError(
            """
                Unable to identify a viable item type for sample testing
            """
        )
    else:
        return item_types[0]["id"]


@pytest.fixture(scope="session")
def real_relationship(get_test_jama_client, real_project):
    if "RELATIONSHIP_ID" in os.environ:
        return os.environ.get("RELATIONSHIP_ID")
    relationships_api = RelationshipsAPI(get_test_jama_client)
    relationships = relationships_api.get_relationships(project_id=real_project).data
    if relationships == []:
        raise ValueError(
            """
                Unable to identify a viable relationship for sample testing
            """
        )
    else:
        return relationships[0]["id"]


@pytest.fixture(scope="session")
def real_relationship_type(get_test_jama_client):
    if "RELATIONSHIP_TYPE_ID" in os.environ:
        return os.environ.get("RELATIONSHIP_TYPE_ID")
    relationships_api = RelationshipsAPI(get_test_jama_client)
    relationship_types = relationships_api.get_relationship_types().data
    if relationship_types == []:
        raise ValueError(
            """
                Unable to identify a viable relationship type for sample testing
            """
        )
    else:
        return relationship_types[0]["id"]


@pytest.fixture(scope="session")
def real_tag(get_test_jama_client, real_project):
    if "TAG_ID" in os.environ:
        return os.environ.get("TAG_ID")
    tags_api = TagsAPI(get_test_jama_client)
    tags = tags_api.get_tags(project_id=real_project).data
    if tags == []:
        raise ValueError(
            """
                Unable to identify a viable tag for sample testing
            """
        )
    else:
        return tags[0]["id"]


@pytest.fixture(scope="session")
def current_user(get_test_jama_client):
    users_api = UsersAPI(get_test_jama_client)
    user = users_api.get_current_user().data
    yield user
