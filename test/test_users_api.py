from py_jama_client.apis.users_api import UsersAPI
import pytest

@pytest.fixture(scope="function")
def users_api(get_test_jama_client):
    api_instance = UsersAPI(get_test_jama_client)
    return api_instance


def test_get_current_user(users_api):
    user = users_api.get_current_user()
    assert user.data is not None


def test_get_current_user_favorite_filters(users_api):
    filters = users_api.get_current_user_favorite_filters()
    assert filters.data is not None

def test_get_users(users_api):
    response = users_api.get_users()
    assert response.data is not None


def test_get_users_by_project(users_api, real_project):
    response = users_api.get_users(params=
                                   {"project": real_project})
    assert response.data is not None


def test_get_users_by_username(users_api, real_project, current_user):
    response = users_api.get_users(params={
                                   "project": real_project,
                                   "username": current_user['username']})
    assert current_user in response.data


def test_get_users_by_email(users_api, real_project, current_user):
    response = users_api.get_users(params={
                                   "project": real_project,
                                   "email": current_user['email']})
    assert current_user in response.data


def test_get_users_by_first_name(users_api, real_project, current_user):
    response = users_api.get_users(params={
                                           "project": real_project,
                                           "firstName": current_user['firstName']})
    assert current_user in response.data


def test_get_users_by_last_name(users_api, real_project, current_user):
    response = users_api.get_users(params={
                                           "project": real_project,
                                           "lastName": current_user['lastName']})
    assert current_user in response.data


def test_get_users_by_license_type(users_api, real_project, current_user):
    response = users_api.get_users(params={
                                           "project": real_project,
                                           "licenseType": current_user['licenseType']})
    assert current_user in response.data


def test_get_user(users_api, current_user):
    response = users_api.get_user(user_id=current_user['id'])
    assert current_user == response.data
