import pytest
import requests as req_lib
from conftest import FakeResponse

from linkedin_cli.auth import AuthService
from linkedin_cli.client import LinkedInClient, LinkedInError
from linkedin_cli.config import load_config
from linkedin_cli.i18n import t
from linkedin_cli.models import AuthToken, MediaAsset, Post


class FakeAuth:
    def __init__(self, person_urn="urn:li:person:123"):
        self._urn = person_urn
        self.calls = 0

    def get_token(self):
        self.calls += 1
        return AuthToken(access_token="acc", refresh_token="ref", expires_in=3600, obtained_at=100)

    def get_person_urn(self):
        return self._urn


@pytest.fixture
def auth():
    return FakeAuth()


@pytest.fixture
def client(auth):
    return LinkedInClient(auth=auth, api_version="202604")


def test_get_person_urn(client):
    assert client.get_person_urn() == "urn:li:person:123"


def test_create_text_post(client, mocker):
    resp = FakeResponse(201, headers={"x-restli-id": "urn:li:share:999"})
    mocker.patch.object(client._session, "request", return_value=resp)

    post = client.create_post("Hello world")

    assert isinstance(post, Post)
    assert post.id == "urn:li:share:999"
    assert post.commentary == "Hello world"
    request_kwargs = client._session.request.call_args.kwargs
    body = request_kwargs["json"]
    assert body["author"] == "urn:li:person:123"
    assert body["commentary"] == "Hello world"
    assert body["visibility"] == "PUBLIC"
    assert body["distribution"]["feedDistribution"] == "MAIN_FEED"
    assert body["lifecycleState"] == "PUBLISHED"
    assert "content" not in body


def test_create_image_post(client, mocker):
    resp = FakeResponse(201, headers={"x-restli-id": "urn:li:share:999"})
    mocker.patch.object(client._session, "request", return_value=resp)

    post = client.create_post("Check this", image_urn="urn:li:image:IMG", alt_text="a photo")

    assert post.media_id == "urn:li:image:IMG"
    body = client._session.request.call_args.kwargs["json"]
    assert body["content"]["media"]["id"] == "urn:li:image:IMG"
    assert body["content"]["media"]["altText"] == "a photo"


def test_create_post_headers(client, mocker):
    resp = FakeResponse(201, headers={"x-restli-id": "urn:li:share:1"})
    mocker.patch.object(client._session, "request", return_value=resp)

    client.create_post("x")

    headers = client._session.request.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer acc"
    assert headers["LinkedIn-Version"] == "202604"
    assert headers["X-Restli-Protocol-Version"] == "2.0.0"
    assert headers["Content-Type"] == "application/json"


def test_create_post_missing_id(client, mocker):
    resp = FakeResponse(201)
    mocker.patch.object(client._session, "request", return_value=resp)
    with pytest.raises(LinkedInError):
        client.create_post("x")


def test_create_post_api_error(client, mocker):
    resp = FakeResponse(403, {"message": "no"})
    mocker.patch.object(client._session, "request", return_value=resp)
    with pytest.raises(LinkedInError):
        client.create_post("x")


def test_create_post_escapes_reserved(client, mocker):
    resp = FakeResponse(201, headers={"x-restli-id": "urn:li:share:999"})
    mocker.patch.object(client._session, "request", return_value=resp)

    post = client.create_post("veja (esta parte)")

    request_kwargs = client._session.request.call_args.kwargs
    assert request_kwargs["json"]["commentary"] == "veja \\(esta parte\\)"
    assert post.commentary == "veja \\(esta parte\\)"


def test_create_post_skip_escape_reserved(client, mocker):
    resp = FakeResponse(201, headers={"x-restli-id": "urn:li:share:999"})
    mocker.patch.object(client._session, "request", return_value=resp)

    client.create_post("veja (esta parte)", escape_reserved=False)

    request_kwargs = client._session.request.call_args.kwargs
    assert request_kwargs["json"]["commentary"] == "veja (esta parte)"


def test_upload_image(client, tmp_path, mocker):
    image = tmp_path / "img.png"
    image.write_bytes(b"\x89PNG")
    init_resp = FakeResponse(
        200,
        {"value": {"uploadUrl": "https://upload.example/up", "image": "urn:li:image:IMG"}},
    )
    upload_resp = FakeResponse(201)
    mocker.patch.object(client._session, "request", side_effect=[init_resp, upload_resp])

    asset = client.upload_image(str(image))

    assert isinstance(asset, MediaAsset)
    assert asset.image_urn == "urn:li:image:IMG"
    calls = client._session.request.call_args_list
    assert calls[0].args[0] == "POST"
    assert calls[0].args[1] == "https://api.linkedin.com/rest/images?action=initializeUpload"
    assert calls[0].kwargs["json"] == {"initializeUploadRequest": {"owner": "urn:li:person:123"}}
    assert calls[1].args[0] == "PUT"
    assert calls[1].args[1] == "https://upload.example/up"
    assert calls[1].kwargs["headers"]["Content-Type"] == "image/png"


def test_upload_image_init_error(client, tmp_path, mocker):
    image = tmp_path / "img.png"
    image.write_bytes(b"x")
    mocker.patch.object(
        client._session, "request", return_value=FakeResponse(400, {"message": "bad"})
    )
    with pytest.raises(LinkedInError):
        client.upload_image(str(image))


def test_upload_image_missing_url(client, tmp_path, mocker):
    image = tmp_path / "img.png"
    image.write_bytes(b"x")
    mocker.patch.object(
        client._session,
        "request",
        return_value=FakeResponse(200, {"value": {}}),
    )
    with pytest.raises(LinkedInError):
        client.upload_image(str(image))


def test_upload_image_missing_file(client, tmp_path, mocker):
    mocker.patch.object(
        client._session,
        "request",
        return_value=FakeResponse(
            200,
            {"value": {"uploadUrl": "https://upload.example/up", "image": "urn:li:image:IMG"}},
        ),
    )
    with pytest.raises(LinkedInError):
        client.upload_image(str(tmp_path / "missing.png"))


def test_upload_image_upload_fails(client, tmp_path, mocker):
    image = tmp_path / "img.png"
    image.write_bytes(b"x")
    init_resp = FakeResponse(
        200,
        {"value": {"uploadUrl": "https://upload.example/up", "image": "urn:li:image:IMG"}},
    )
    upload_resp = FakeResponse(500)
    mocker.patch.object(client._session, "request", side_effect=[init_resp, upload_resp])
    with pytest.raises(LinkedInError):
        client.upload_image(str(image))


def test_list_posts(client, mocker):
    resp = FakeResponse(
        200,
        {
            "elements": [
                {
                    "id": "urn:li:share:1",
                    "commentary": "hello",
                    "visibility": "PUBLIC",
                    "publishedAt": 123,
                    "content": {"media": {"id": "urn:li:image:A"}},
                }
            ]
        },
    )
    mocker.patch.object(client._session, "request", return_value=resp)

    posts = client.list_posts(max_count=5)

    assert len(posts) == 1
    assert posts[0].id == "urn:li:share:1"
    assert posts[0].media_id == "urn:li:image:A"
    headers = client._session.request.call_args.kwargs["headers"]
    assert headers["X-RestLi-Method"] == "FINDER"
    params = client._session.request.call_args.kwargs["params"]
    assert params["q"] == "author"
    assert params["count"] == 5


def test_list_posts_forbidden(client, mocker):
    mocker.patch.object(client._session, "request", return_value=FakeResponse(403))
    with pytest.raises(LinkedInError) as exc:
        client.list_posts()
    assert "r_member_social" in str(exc.value)


def test_list_posts_error(client, mocker):
    mocker.patch.object(client._session, "request", return_value=FakeResponse(500))
    with pytest.raises(LinkedInError):
        client.list_posts()


def test_get_post(client, mocker):
    resp = FakeResponse(
        200,
        {"id": "urn:li:share:7", "commentary": "hi", "visibility": "CONNECTIONS", "publishedAt": 1},
    )
    mocker.patch.object(client._session, "request", return_value=resp)

    post = client.get_post("urn:li:share:7")

    assert post.id == "urn:li:share:7"
    assert post.commentary == "hi"
    assert post.visibility == "CONNECTIONS"
    url = client._session.request.call_args.args[1]
    assert "urn%3Ali%3Ashare%3A7" in url


def test_get_post_not_found(client, mocker):
    mocker.patch.object(client._session, "request", return_value=FakeResponse(404))
    with pytest.raises(LinkedInError):
        client.get_post("urn:li:share:404")


def test_delete_post(client, mocker):
    mocker.patch.object(client._session, "request", return_value=FakeResponse(204))

    client.delete_post("urn:li:share:7")

    headers = client._session.request.call_args.kwargs["headers"]
    assert headers["X-RestLi-Method"] == "DELETE"
    assert client._session.request.call_args.args[0] == "DELETE"


def test_delete_post_error(client, mocker):
    mocker.patch.object(client._session, "request", return_value=FakeResponse(500))
    with pytest.raises(LinkedInError):
        client.delete_post("urn:li:share:7")


def test_request_wraps_network_errors(client, mocker):
    mocker.patch.object(client._session, "request", side_effect=req_lib.ConnectionError("down"))
    with pytest.raises(LinkedInError):
        client._request("GET", "https://api.linkedin.com/rest/posts")


@pytest.mark.parametrize(
    ("code", "key"),
    [
        (401, "error_unauthorized"),
        (403, "error_permission"),
        (404, "error_not_found"),
        (429, "error_rate_limited"),
        (422, "error_invalid_request"),
        (500, "error_server"),
    ],
)
def test_raise_for_status_messages(client, code, key):
    resp = FakeResponse(code, {"message": "boom"})
    expected = t(load_config().language, key, message="boom", resource=str(resp.url), code=code)
    with pytest.raises(LinkedInError) as exc:
        client._raise_for_status(resp)
    assert str(exc.value) == expected


def test_raise_for_status_non_json(client):
    resp = FakeResponse(500, text="plain error")
    with pytest.raises(LinkedInError):
        client._raise_for_status(resp)


def test_default_client_uses_config_auth(data_dir):
    client = LinkedInClient()
    assert isinstance(client.auth, AuthService)
    assert client.api_version == "202604"
