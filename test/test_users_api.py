from py_jama_client.apis.users_api import UsersAPI


def test_get_current_user(get_test_jama_client):
    users_api = UsersAPI(get_test_jama_client)
    user = users_api.get_current_user()
    assert user.data is not None


def test_get_current_user_favorite_filters(get_test_jama_client):
    users_api = UsersAPI(get_test_jama_client)
    user = users_api.get_current_user()
    assert user.data is not None


def test_get_users(get_test_jama_client):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users()
    assert response.data is not None


def test_get_users_by_project(get_test_jama_client, real_project):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users(params=
                                   {"project": real_project})
    assert response.data is not None


def test_get_users_by_username(get_test_jama_client, real_project, current_user):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users(params={
                                   "project": real_project,
                                   "username": current_user['username']})
    assert current_user in response.data


def test_get_users_by_email(get_test_jama_client, real_project, current_user):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users(params={
                                   "project": real_project,
                                   "email": current_user['email']})
    assert current_user in response.data


def test_get_users_by_first_name(get_test_jama_client,
                                 real_project,
                                 current_user):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users(params={
                                           "project": real_project,
                                           "firstName": current_user['firstName']})
    assert current_user in response.data


def test_get_users_by_last_name(get_test_jama_client,
                                real_project,
                                current_user):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users(params={
                                           "project": real_project,
                                           "lastName": current_user['lastName']})
    assert current_user in response.data


def test_get_users_by_license_type(get_test_jama_client,
                                   real_project,
                                   current_user):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users(params={
                                           "project": real_project,
                                           "licenseType": current_user['licenseType']})
    assert current_user in response.data


def test_get_user(get_test_jama_client, current_user):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_user(user_id=current_user['id'])
    assert current_user == response.data
