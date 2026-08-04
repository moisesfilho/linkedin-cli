import pytest

from linkedin_cli.models import (
    QUEUE_STATUS_PENDING,
    QUEUE_STATUSES,
    VISIBILITIES,
    VISIBILITY_CONNECTIONS,
    VISIBILITY_PUBLIC,
    AuthToken,
    MediaAsset,
    Post,
    QueuedPost,
)


def test_post_url():
    post = Post(id="urn:li:share:123", commentary="hello")
    assert post.url == "https://www.linkedin.com/feed/update/urn:li:share:123/"


def test_post_defaults():
    post = Post(id="urn:li:share:123")
    assert post.commentary == ""
    assert post.visibility == VISIBILITY_PUBLIC
    assert post.published_at is None
    assert post.media_id is None
    assert post.lifecycle_state == "PUBLISHED"


def test_queued_post_to_dict():
    q = QueuedPost(id="q1", commentary="hello", scheduled_at="2026-08-10 09:00")
    assert q.to_dict() == {
        "id": "q1",
        "commentary": "hello",
        "scheduled_at": "2026-08-10 09:00",
        "status": QUEUE_STATUS_PENDING,
        "image_path": None,
        "alt_text": None,
        "visibility": VISIBILITY_PUBLIC,
        "post_id": None,
        "error": None,
    }


def test_queued_post_roundtrip():
    original = QueuedPost(
        id="q1",
        commentary="hello",
        scheduled_at="2026-08-10 09:00",
        image_path="/tmp/img.png",
        alt_text="alt",
        visibility=VISIBILITY_CONNECTIONS,
        status="published",
        post_id="urn:li:share:1",
        error=None,
    )
    restored = QueuedPost.from_dict(original.to_dict())

    assert restored == original


def test_queued_post_from_dict_with_defaults():
    restored = QueuedPost.from_dict({"id": "q1", "commentary": "hi", "scheduled_at": "t"})

    assert restored.status == QUEUE_STATUS_PENDING
    assert restored.visibility == VISIBILITY_PUBLIC
    assert restored.image_path is None
    assert restored.post_id is None
    assert restored.error is None


def test_media_asset_from_response():
    asset = MediaAsset.from_response(
        {
            "value": {
                "uploadUrl": "https://upload.example/1",
                "uploadUrlExpiresAt": 123456,
                "image": "urn:li:image:ABC",
            }
        }
    )
    assert asset.image_urn == "urn:li:image:ABC"
    assert asset.upload_url == "https://upload.example/1"
    assert asset.expires_at == 123456


def test_media_asset_from_empty_response():
    asset = MediaAsset.from_response({})
    assert asset.image_urn == ""
    assert asset.upload_url == ""
    assert asset.expires_at is None


def test_auth_token_from_response():
    token = AuthToken.from_response(
        {"access_token": "tok", "refresh_token": "ref", "expires_in": 3600}
    )
    assert token.access_token == "tok"
    assert token.refresh_token == "ref"
    assert token.expires_in == 3600


def test_auth_token_from_partial_response():
    token = AuthToken.from_response({})
    assert token.access_token == ""
    assert token.refresh_token is None
    assert token.expires_in == 0


def test_auth_token_is_expired():
    token = AuthToken(access_token="a", refresh_token="r", expires_in=100, obtained_at=50)
    assert token.is_expired(now=149) is False
    assert token.is_expired(now=151) is True


def test_auth_token_is_expired_no_expiry():
    token = AuthToken(access_token="a", refresh_token="r", expires_in=0, obtained_at=100)
    assert token.is_expired(now=10**12) is False


@pytest.mark.parametrize("status", QUEUE_STATUSES)
def test_queue_statuses_valid(status):
    assert status in QUEUE_STATUSES


@pytest.mark.parametrize("visibility", VISIBILITIES)
def test_visibilities_valid(visibility):
    assert visibility in VISIBILITIES
