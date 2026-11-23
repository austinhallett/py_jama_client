import warnings
from unittest.mock import Mock

import pytest

from py_jama_client.apis.attachments_api import AttachmentsAPI
from py_jama_client.exceptions import (
    APIException,
    APIServerException,
    CoreException,
    ResourceNotFoundException,
)

MISSING_ATTACHMENT_ID = 2147483647


@pytest.fixture(scope="function")
def attachments_api(get_test_jama_client, bounded_pages):
    return AttachmentsAPI(get_test_jama_client)


def test_get_attachment(attachments_api, real_attachment, real_project):
    response = attachments_api.get_attachment(attachment_id=real_attachment)
    assert response.data["id"] == real_attachment
    assert response.data["type"] == "attachments"
    assert response.data["project"] == real_project
    assert "name" in response.data["fields"]
    assert isinstance(response.data["fileName"], str)
    assert isinstance(response.data["mimeType"], str)
    assert isinstance(response.data["fileSize"], int)
    assert response.data["fileSize"] >= 0


def test_get_attachment_missing_attachment(attachments_api):
    with pytest.raises(ResourceNotFoundException):
        attachments_api.get_attachment(attachment_id=MISSING_ATTACHMENT_ID)


def test_get_attachment_file(attachments_api, real_attachment):
    file_size = attachments_api.get_attachment(attachment_id=real_attachment).data[
        "fileSize"
    ]
    content = attachments_api.get_attachment_file(attachment_id=real_attachment)
    assert isinstance(content, bytes)
    assert len(content) == file_size


def test_get_attachment_file_does_not_mutate_params(attachments_api, real_attachment):
    params = {}
    attachments_api.get_attachment_file(attachment_id=real_attachment, params=params)
    assert params == {}


def test_get_file(attachments_api, real_attachment):
    attachment = attachments_api.get_attachment(attachment_id=real_attachment).data
    host = attachments_api.client._host_name.removesuffix("/rest/v1/")
    file_id = attachment["fields"]["attachment"]
    url = f"{host}/attachment/{file_id}/{attachment['fileName']}"
    content = attachments_api.get_file(url)
    assert isinstance(content, bytes)
    assert len(content) == attachment["fileSize"]


def test_get_file_sends_url_without_mutating_params():
    client = Mock()
    client.get.return_value.status_code = 200
    client.get.return_value.content = b"data"
    params = {"x": "1"}
    content = AttachmentsAPI(client).get_file(
        "https://jama.example.com/f", params=params
    )
    assert content == b"data"
    assert client.get.call_args.args == (
        "files",
        {"x": "1", "url": "https://jama.example.com/f"},
    )
    assert params == {"x": "1"}


def test_get_attachment_file_missing_attachment(attachments_api):
    with pytest.raises(ResourceNotFoundException):
        attachments_api.get_attachment_file(attachment_id=MISSING_ATTACHMENT_ID)


def test_get_attachment_file_of_non_attachment_item(
    attachments_api, real_attached_item
):
    with pytest.raises(ResourceNotFoundException):
        attachments_api.get_attachment_file(attachment_id=real_attached_item)


def test_get_attachment_lock(attachments_api, real_attachment):
    response = attachments_api.get_attachment_lock(attachment_id=real_attachment)
    assert isinstance(response.data["locked"], bool)


def test_get_attachment_versions(attachments_api, real_attachment):
    response = attachments_api.get_attachment_versions(attachment_id=real_attachment)
    assert len(response.data) >= 1
    assert all(v["item"] == real_attachment for v in response.data)
    assert all(isinstance(v["versionNumber"], int) for v in response.data)


def test_get_attachment_version(attachments_api, real_attachment):
    version_num = attachments_api.get_attachment_versions(
        attachment_id=real_attachment
    ).data[0]["versionNumber"]
    response = attachments_api.get_attachment_version(
        attachment_id=real_attachment, version_num=version_num
    )
    assert response.data["item"] == real_attachment
    assert response.data["versionNumber"] == version_num


def test_get_attachment_version_item(attachments_api, real_attachment, real_project):
    version_num = attachments_api.get_attachment_versions(
        attachment_id=real_attachment
    ).data[0]["versionNumber"]
    response = attachments_api.get_attachment_version_item(
        attachment_id=real_attachment, version_num=version_num
    )
    assert response.data["id"] == real_attachment
    assert response.data["version"] == version_num
    assert response.data["type"] == "versionedattachments"
    assert response.data["project"] == real_project
    assert isinstance(response.data["fileName"], str)
    assert isinstance(response.data["fileSize"], int)
    assert response.data["fileSize"] >= 0
    assert "name" in response.data["fields"]


def test_get_attachment_comments(attachments_api, real_attachment, bounded_pages):
    response = attachments_api.get_attachment_comments(attachment_id=real_attachment)
    total_results = bounded_pages["offset_total"]
    assert len(response.data) == min(total_results, 12)
    assert all({"id", "body", "createdBy"} <= set(c) for c in response.data)


def test_get_attachment_comments_missing_attachment(attachments_api):
    with pytest.raises(ResourceNotFoundException):
        attachments_api.get_attachment_comments(attachment_id=MISSING_ATTACHMENT_ID)


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_attachment(attachment_id=1),
        lambda api: api.get_attachment_file(attachment_id=1),
        lambda api: api.get_attachment_lock(attachment_id=1),
        lambda api: api.get_attachment_version(attachment_id=1, version_num=1),
        lambda api: api.get_attachment_version_item(attachment_id=1, version_num=1),
        lambda api: api.get_file("https://jama.example.com/attachment/1/a.txt"),
    ],
    ids=["attachment", "file", "lock", "version", "version_item", "get_file"],
)
def test_attachment_reads_wrap_core_exception(call):
    client = Mock()
    client.get.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(AttachmentsAPI(client))


SCRATCH_TEXT = b"Scratch attachment for API tests.\n"
# The file name of the scratch attachment 744534.
SCRATCH_FILENAME = "MockAttachment2.txt"


def test_put_attachments_file(attachments_api, real_scratch_attachment, tmp_path):
    upload = tmp_path / SCRATCH_FILENAME
    upload.write_bytes(SCRATCH_TEXT)
    assert (
        attachments_api.put_attachments_file(real_scratch_attachment, str(upload))
        == 200
    )
    attachment = attachments_api.get_attachment(real_scratch_attachment).data
    assert attachment["fileName"] == SCRATCH_FILENAME
    assert attachment["fileSize"] == len(SCRATCH_TEXT)
    assert attachment["mimeType"] == "text/plain"
    assert attachments_api.get_attachment_file(real_scratch_attachment) == SCRATCH_TEXT


def test_put_attachments_file_empty_is_rejected(
    attachments_api, real_scratch_attachment, tmp_path
):
    # Jama's security scan fails on an empty file, so nothing is saved. The
    # exception carries no response body; the cassette holds the scan message.
    upload = tmp_path / SCRATCH_FILENAME
    upload.write_bytes(b"")
    with pytest.raises(APIServerException) as excinfo:
        attachments_api.put_attachments_file(real_scratch_attachment, str(upload))
    assert excinfo.value.status_code == 500
    assert attachments_api.get_attachment_file(real_scratch_attachment) == SCRATCH_TEXT


def test_put_attachment_lock_round_trip(attachments_api, real_scratch_attachment):
    start = attachments_api.get_attachment_lock(real_scratch_attachment).data["locked"]
    locked = False
    try:
        response = attachments_api.put_attachment_lock(real_scratch_attachment, True)
        locked = True
        assert response.meta["status"] == "OK"
        lock = attachments_api.get_attachment_lock(real_scratch_attachment).data
        assert lock["locked"] is True
    finally:
        if locked:
            try:
                attachments_api.put_attachment_lock(real_scratch_attachment, start)
            except Exception as error:  # noqa: BLE001
                warnings.warn(f"could not unlock the scratch attachment: {error}")
    lock = attachments_api.get_attachment_lock(real_scratch_attachment).data
    assert lock["locked"] is start


def test_put_attachments_file_sends_the_file_and_returns_status(tmp_path):
    upload = tmp_path / "upload.txt"
    upload.write_bytes(b"data")
    client = Mock()
    client.put.return_value = Mock(status_code=200)
    params = {"a": 1}
    status = AttachmentsAPI(client).put_attachments_file(5, str(upload), params=params)
    assert status == 200
    args, kwargs = client.put.call_args
    assert args == ("attachments/5/file", {"a": 1})
    assert kwargs["files"]["file"].name == str(upload)
    assert params == {"a": 1}


def test_put_attachment_lock_sends_json_body():
    client = Mock()
    client.put.return_value = Mock(
        status_code=200, json=Mock(return_value={"meta": {}}), text=""
    )
    AttachmentsAPI(client).put_attachment_lock(5, False, params={"a": 1})
    client.put.assert_called_with(
        "attachments/5/lock", {"a": 1}, json={"locked": False}
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda api, path: api.put_attachments_file(5, path),
        lambda api, path: api.put_attachment_lock(5, True),
    ],
    ids=["file", "lock"],
)
def test_attachment_puts_wrap_core_exception(call, tmp_path):
    upload = tmp_path / "upload.txt"
    upload.write_bytes(b"data")
    client = Mock()
    client.put.side_effect = CoreException("boom")
    with pytest.raises(APIException):
        call(AttachmentsAPI(client), str(upload))


def get_all_params(client):
    call = client.get_all.call_args
    return call.kwargs["params"] if "params" in call.kwargs else call.args[1]


def test_get_attachment_comments_maps_root_comments_only():
    client = Mock()
    params = {"rootCommentsOnly": False}
    AttachmentsAPI(client).get_attachment_comments(
        5, params=params, root_comments_only=True
    )
    assert get_all_params(client) == {"rootCommentsOnly": True}
    assert params == {"rootCommentsOnly": False}
    AttachmentsAPI(client).get_attachment_comments(5)
    assert get_all_params(client) is None
