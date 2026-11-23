from unittest.mock import Mock

import pytest

from py_jama_client.apis.system_api import SystemAPI
from py_jama_client.exceptions import (
    APIException,
    CoreException,
    UnauthorizedException,
)

DOMAINS = ["https://app.example.com", "https://www.example.com"]


@pytest.fixture(scope="function")
def system_api(get_test_jama_client):
    return SystemAPI(get_test_jama_client)


def test_get_cors_domains_docs(system_api):
    response = system_api.get_cors_domains()
    assert response.data == {"domains": DOMAINS}
    assert response.meta["status"] == "OK"


def test_post_cors_domains_docs(system_api):
    # The docs give no example request body, only the CrossOriginDomainWhiteList
    # model (domains).
    response = system_api.post_cors_domains(DOMAINS)
    assert response.meta["status"] == "OK"
    assert response.data == {}


def offline_api():
    client = Mock()
    for verb in ("get", "post"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"meta": {}}), text=""
        )
    return SystemAPI(client), client


@pytest.mark.parametrize(
    ("call", "verb"),
    [
        (lambda api, params: api.get_cors_domains(params=params), "get"),
        (lambda api, params: api.post_cors_domains([], params=params), "post"),
    ],
    ids=["get", "post"],
)
def test_forwards_params_untouched(call, verb):
    api, client = offline_api()
    params = {"a": 1}
    call(api, params)
    assert getattr(client, verb).call_args.args[1] == {"a": 1}
    assert params == {"a": 1}


@pytest.mark.parametrize(
    "call",
    [lambda api: api.get_cors_domains(), lambda api: api.post_cors_domains([])],
    ids=["get", "post"],
)
def test_wraps_core_exception(call):
    api, client = offline_api()
    for verb in ("get", "post"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_get_cors_domains_without_permission(system_api):
    with pytest.raises(UnauthorizedException):
        system_api.get_cors_domains()
