import inspect
from unittest.mock import Mock

import pytest

from py_jama_client import apis
from py_jama_client.apis._include import with_include, with_query

INCLUDE = ["data.createdBy"]


def methods_with_include():
    for name in sorted(dir(apis)):
        api = getattr(apis, name)
        if not (inspect.isclass(api) and name.endswith("API")):
            continue
        for method_name, method in inspect.getmembers(api, inspect.isfunction):
            if "include" in inspect.signature(method).parameters:
                yield pytest.param(api, method_name, id=f"{name}.{method_name}")


METHODS = list(methods_with_include())


def test_with_include_leaves_params_alone_without_include():
    params = {"a": 1}
    assert with_include(params, None) is params
    assert with_include(None, None) is None


def test_with_include_adds_include_to_a_copy():
    params = {"a": 1}
    assert with_include(params, ("data.createdBy",)) == {
        "a": 1,
        "include": ["data.createdBy"],
    }
    assert params == {"a": 1}
    assert with_include(None, ["x"]) == {"include": ["x"]}


def test_with_include_keeps_existing_values_and_accepts_a_string():
    params = {"include": "data.project"}
    assert with_include(params, "data.createdBy") == {
        "include": ["data.project", "data.createdBy"]
    }
    assert params == {"include": "data.project"}


@pytest.mark.parametrize(
    ("existing", "expected"),
    [
        (None, ["data.createdBy"]),
        (7, [7, "data.createdBy"]),
        ("data.project", ["data.project", "data.createdBy"]),
        (("a", "b"), ["a", "b", "data.createdBy"]),
    ],
)
def test_with_include_accepts_any_existing_include(existing, expected):
    params = {"include": existing}
    assert with_include(params, "data.createdBy") == {"include": expected}
    assert params == {"include": existing}


def test_with_include_does_not_mutate_an_existing_include_list():
    existing = ["data.project"]
    with_include({"include": existing}, ["data.createdBy"])
    assert existing == ["data.project"]


def test_with_query_leaves_params_alone_when_every_value_is_none():
    params = {"a": 1}
    assert with_query(params, x=None, y=None) is params
    assert with_query(None, x=None) is None


def test_with_query_adds_given_values_to_a_copy_and_they_win():
    params = {"a": 1, "x": 0}
    assert with_query(params, x=False, y=None, z=[1, 2]) == {
        "a": 1,
        "x": False,
        "z": [1, 2],
    }
    assert params == {"a": 1, "x": 0}
    assert with_query(None, x=1) == {"x": 1}


def test_every_include_parameter_is_keyword_only_and_optional():
    assert len(METHODS) >= 121
    for case in METHODS:
        api, name = case.values
        assert isinstance(name, str)
        parameter = inspect.signature(getattr(api, name)).parameters["include"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None


def mock_client():
    client = Mock()
    response = Mock(status_code=200, text="")
    response.json.return_value = {"data": {}, "meta": {}, "links": {}, "linked": {}}
    for verb in ("get", "post", "put", "patch", "delete"):
        getattr(client, verb).return_value = response
    return client


def sent_params(client):
    """Every dict passed (positionally or as params=) to the mock client."""
    for call in client.mock_calls:
        for value in [*call.args, *call.kwargs.values()]:
            if isinstance(value, dict):
                yield value


@pytest.mark.parametrize(("api", "name"), METHODS)
def test_every_method_sends_include(api, name):
    client = mock_client()
    method = getattr(api(client), name)
    required = [
        p
        for p in inspect.signature(method).parameters.values()
        if p.kind is p.POSITIONAL_OR_KEYWORD and p.default is p.empty
    ]
    extra = {"params": {"testCycle": 1}} if name == "get_test_runs" else {}
    method(*[1] * len(required), include=INCLUDE, **extra)
    assert any(p.get("include") == INCLUDE for p in sent_params(client)), name
