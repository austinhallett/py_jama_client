from unittest.mock import Mock

import pytest

from py_jama_client.apis.users_api import UsersAPI
from py_jama_client.exceptions import APIException, CoreException, UnauthorizedException


@pytest.fixture(scope="function")
def users_api(get_test_jama_client):
    api_instance = UsersAPI(get_test_jama_client)
    return api_instance


def test_get_current_user(users_api):
    user = users_api.get_current_user()
    assert user.data is not None


def test_get_current_user_favorite_filters(users_api):
    filters = users_api.get_current_user_favorite_filters()
    assert filters.data


def test_get_users_without_permission(users_api):
    with pytest.raises(UnauthorizedException) as error:
        users_api.get_users()
    assert error.value.reason
    assert "permission" in error.value.reason.lower()


def test_get_users_by_project(users_api, real_project, bounded_pages):
    response = users_api.get_users(params={"project": real_project})
    total_results = bounded_pages["offset_total"]
    assert len(response.data) == min(12, total_results)
    assert all(
        {"id", "username", "firstName", "lastName"} <= set(u) for u in response.data
    )
    assert {u["type"] for u in response.data} == {"users"}


def test_get_users_by_username(users_api, real_project, current_user):
    response = users_api.get_users(
        params={"project": real_project, "username": current_user["username"]}
    )
    assert current_user in response.data


def test_get_users_by_email(users_api, real_project, current_user):
    response = users_api.get_users(
        params={"project": real_project, "email": current_user["email"]}
    )
    assert current_user in response.data


def test_get_users_by_first_name(users_api, real_project, current_user):
    response = users_api.get_users(
        params={"project": real_project, "firstName": current_user["firstName"]}
    )
    assert current_user in response.data


def test_get_users_by_last_name(users_api, real_project, current_user):
    response = users_api.get_users(
        params={"project": real_project, "lastName": current_user["lastName"]}
    )
    assert current_user in response.data


def test_get_users_by_license_type(users_api, real_project, current_user):
    response = users_api.get_users(
        params={"project": real_project, "licenseType": current_user["licenseType"]}
    )
    assert current_user in response.data


def test_get_user(users_api, current_user):
    response = users_api.get_user(user_id=current_user["id"])
    assert current_user == response.data


def test_get_users_synthetic(users_api):
    response = users_api.get_users(allowed_results_per_page=2)
    assert [user["id"] for user in response.data] == [1, 2, 3]
    assert response.data[1]["username"] == "user2"
    assert {user["type"] for user in response.data} == {"users"}


def test_get_user_custom_data_docs(users_api):
    response = users_api.get_user_custom_data(5)
    assert response.data == [
        {"name": "Example name 1", "value": "Example value 1"},
        {"name": "Example name 2", "value": "Example value 2"},
    ]
    assert response.meta["pageInfo"]["totalResults"] == 2


def test_put_user_custom_data_docs(users_api):
    # The docs give no example request body, only "List"; entries are built
    # from the UserCustomData model (name, value).
    status = users_api.put_user_custom_data(
        5,
        [
            {"name": "Example name 1", "value": "Example value 1"},
            {"name": "Example name 2", "value": "Example value 2"},
        ],
    )
    assert status == 200


def offline_custom_data_api():
    client = Mock()
    client.get_all.return_value = Mock()
    for verb in ("get", "put"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"data": [], "meta": {}}), text=""
        )
    return UsersAPI(client), client


@pytest.mark.parametrize(
    ("call", "verb"),
    [
        (lambda api, params: api.put_user_custom_data(5, [], params=params), "put"),
    ],
    ids=["put"],
)
def test_custom_data_forwards_params_untouched(call, verb):
    api, client = offline_custom_data_api()
    params = {"a": 1}
    call(api, params)
    assert getattr(client, verb).call_args.args[1] == {"a": 1}
    assert params == {"a": 1}


def test_get_user_custom_data_pages_with_params_untouched():
    api, client = offline_custom_data_api()
    params = {"a": 1}
    api.get_user_custom_data(5, params=params, allowed_results_per_page=7)
    assert client.get_all.call_args.args == ("users/5/customData",)
    assert client.get_all.call_args.kwargs["params"] == {"a": 1}
    assert client.get_all.call_args.kwargs["allowed_results_per_page"] == 7
    assert params == {"a": 1}


@pytest.mark.parametrize(
    "call",
    [lambda api: api.put_user_custom_data(5, [])],
    ids=["put"],
)
def test_custom_data_wraps_core_exception(call):
    api, client = offline_custom_data_api()
    client.put.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_post_user_docs(users_api):
    response = users_api.post_user(
        "example",
        "Example password 1",
        "Example",
        "User",
        "example-email",
        "NAMED",
    )
    assert response.data == 0
    assert response.meta["status"] == "OK"


def test_put_user_docs(users_api):
    status = users_api.put_user(
        5,
        "example",
        "Example password 2",
        "Example",
        "User",
        "example-email",
        phone="555-0100",
        title="Engineer",
        location="Remote",
    )
    assert status == 200


def test_put_user_active_docs(users_api):
    assert users_api.put_user_active(5, False) == 200


def offline_user_api():
    client = Mock()
    for verb in ("get", "post", "put"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
        )
    return UsersAPI(client), client


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_user(5),
        lambda api: api.get_current_user(),
        lambda api: api.post_user("u", "p", "f", "l", "e", "NAMED"),
        lambda api: api.put_user(5, "u", "p", "f", "l", "e"),
        lambda api: api.put_user_active(5, True),
    ],
    ids=["get_user", "get_current_user", "post_user", "put_user", "put_user_active"],
)
def test_users_wrap_core_exception(call):
    api, client = offline_user_api()
    for verb in ("get", "post", "put"):
        getattr(client, verb).side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(api)


def test_post_user_sends_optional_fields_as_null():
    api, client = offline_user_api()
    api.post_user("u", "p", "f", "l", "e", "FLOATING")
    assert client.post.call_args.kwargs["json"] == {
        "username": "u",
        "password": "p",
        "firstName": "f",
        "lastName": "l",
        "email": "e",
        "phone": None,
        "title": None,
        "location": None,
        "licenseType": "FLOATING",
    }


def test_get_user_custom_data_without_permission(users_api, current_user):
    with pytest.raises(UnauthorizedException):
        users_api.get_user_custom_data(current_user["id"])


def offline_api():
    client = Mock()
    client.get_all.return_value = Mock()
    for verb in ("post", "put"):
        getattr(client, verb).return_value = Mock(
            status_code=200, json=Mock(return_value={"data": {}, "meta": {}}), text=""
        )
    return UsersAPI(client), client


def test_get_users_maps_filters_to_query_parameters():
    api, client = offline_api()
    params = {"username": "old", "a": 1}
    api.get_users(
        params=params,
        username="u",
        email="email-1",
        first_name="F",
        last_name="L",
        license_type="NAMED",
        include_inactive=False,
        project=3,
    )
    assert client.get_all.call_args.args[1] == {
        "username": "u",
        "email": "email-1",
        "firstName": "F",
        "lastName": "L",
        "licenseType": "NAMED",
        "includeInactive": False,
        "project": 3,
        "a": 1,
    }
    assert params == {"username": "old", "a": 1}


def test_get_users_sends_no_filters_by_default():
    api, client = offline_api()
    params = {"a": 1}
    api.get_users(params=params)
    assert client.get_all.call_args.args[1] is params
    api.get_users()
    assert client.get_all.call_args.args[1] is None


USER = ("u", "pw", "F", "L", "email-1")
AUTHENTICATION_TYPE = {"id": 1, "name": "LDAP"}
CUSTOM_DATA = [{"name": "k", "value": "v"}]


def test_post_user_sends_authentication_type_and_custom_data():
    api, client = offline_api()
    api.post_user(
        *USER,
        "NAMED",
        authentication_type=AUTHENTICATION_TYPE,
        custom_data=CUSTOM_DATA,
    )
    body = client.post.call_args.kwargs["json"]
    assert body["authenticationType"] == AUTHENTICATION_TYPE
    assert body["customData"] == CUSTOM_DATA


def test_post_user_leaves_new_fields_out_when_none():
    api, client = offline_api()
    api.post_user(*USER, "NAMED")
    body = client.post.call_args.kwargs["json"]
    assert "authenticationType" not in body
    assert "customData" not in body


def test_put_user_sends_authentication_type_custom_data_and_license_type():
    api, client = offline_api()
    api.put_user(
        5,
        *USER,
        authentication_type=AUTHENTICATION_TYPE,
        custom_data=CUSTOM_DATA,
        license_type="FLOATING",
    )
    body = client.put.call_args.kwargs["json"]
    assert body["authenticationType"] == AUTHENTICATION_TYPE
    assert body["customData"] == CUSTOM_DATA
    assert body["licenseType"] == "FLOATING"


def test_put_user_leaves_new_fields_out_when_none():
    api, client = offline_api()
    api.put_user(5, *USER)
    body = client.put.call_args.kwargs["json"]
    for key in ("authenticationType", "customData", "licenseType"):
        assert key not in body
