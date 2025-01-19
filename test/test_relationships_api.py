from py_jama_client.apis.relationships_api import RelationshipsAPI


def test_get_relationships(get_test_jama_client, real_project):
    relationships_api = RelationshipsAPI(get_test_jama_client)
    response = relationships_api.get_relationships(
        project_id=real_project)
    assert response.data != []


def test_get_relationship(get_test_jama_client, real_relationship):
    relationships_api = RelationshipsAPI(get_test_jama_client)
    response = relationships_api.get_relationship(
        relationship_id=real_relationship)
    assert response.data != []


def test_get_relationship_types(get_test_jama_client):
    relationships_api = RelationshipsAPI(get_test_jama_client)
    response = relationships_api.get_relationship_types()
    assert response.data != []


def test_get_relationship_type(get_test_jama_client, real_relationship_type):
    relationships_api = RelationshipsAPI(get_test_jama_client)
    response = relationships_api.get_relationship_type(
        relationship_type_id=real_relationship_type)
    assert response.data != []
