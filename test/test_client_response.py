from py_jama_client.response import ClientResponse


def test_client_response(get_example_client_response):
    assert "pageInfo" in get_example_client_response.meta


def test_client_to_dict(get_example_client_response):
    assert "pageInfo" in get_example_client_response.to_dict()["meta"]


def test_client_combination(get_example_client_response):
    new_response = ClientResponse(
        meta={"new": "meta"},
        links={"new": "links"},
        linked={"new": "linked"},
        data=[{"id": 1}],
    )
    combined_response = get_example_client_response + new_response
    assert "pageInfo" in combined_response.meta
    assert "new" in combined_response.meta
    assert "data" in combined_response.to_dict()
    assert len(combined_response.data) == 3
    assert combined_response.data[0]["id"] == 50621
    assert combined_response.data[2]["id"] == 1
