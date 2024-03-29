from py_jama_client.apis.users_api import UsersAPI


def test_get_current_user(get_test_jama_client):
    users_api = UsersAPI(get_test_jama_client)
    user = users_api.get_current_user()
    assert user.data is not None


def test_get_users(get_test_jama_client):
    users_api = UsersAPI(get_test_jama_client)
    response = users_api.get_users()
    assert response.data is not None
