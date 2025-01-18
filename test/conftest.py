import os
import ssl

import pytest

from py_jama_client.client import JamaClient
from py_jama_client.response import ClientResponse


@pytest.fixture(autouse=True)
def env_vars():
    if os.getenv("CLIENT_ID") is None and os.getenv("CLIENT_SECRET") is None:
        raise ValueError(
            """
                Please set environment variables 'client_id' and
                'client_secret' to run tests properly.
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
        oauth=True,
    )

    yield client


@pytest.fixture(scope="session")
def get_example_client_response():
    return ClientResponse(
        meta={
            "status": "OK",
            "timestamp": "2024-01-24T14:19:40.043+0000",
            "pageInfo": {"startIndex": 0,
                         "resultCount": 20,
                         "totalResults": 515},
        },
        links={
            "data.itemType": {
                "type": "itemtypes",
                "href": ("https://silabs.jamacloud.com/rest/v1/itemtypes/"
                         "{data.itemType}"),
            },
            "data.location.parent.project": {
                "type": "projects",
                "href": ("https://silabs.jamacloud.com/rest/v1/projects/"
                         "{data.location.parent.project}"),
            },
            "data.fields.verification_method$141": {
                "type": "picklistoptions",
                "href": ("https://silabs.jamacloud.com/rest/v1/"
                         "picklistoptions/"
                         "{data.fields.verification_method$141}"),
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
                "resources": {"self": {
                    "allowed": ["GET", "PUT", "PATCH", "DELETE"]}},
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
                "resources": {"self": {
                    "allowed": ["GET", "PUT", "PATCH", "DELETE"]}},
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
