import time
from dataclasses import dataclass
from typing import Any

QUEUE_STATUS_PENDING = "pending"
QUEUE_STATUS_PUBLISHING = "publishing"
QUEUE_STATUS_PUBLISHED = "published"
QUEUE_STATUS_FAILED = "failed"
QUEUE_STATUSES = (
    QUEUE_STATUS_PENDING,
    QUEUE_STATUS_PUBLISHING,
    QUEUE_STATUS_PUBLISHED,
    QUEUE_STATUS_FAILED,
)

VISIBILITY_PUBLIC = "PUBLIC"
VISIBILITY_CONNECTIONS = "CONNECTIONS"
VISIBILITIES = (VISIBILITY_PUBLIC, VISIBILITY_CONNECTIONS)


@dataclass
class Post:
    id: str
    commentary: str = ""
    visibility: str = VISIBILITY_PUBLIC
    published_at: int | None = None
    media_id: str | None = None
    lifecycle_state: str = "PUBLISHED"

    @property
    def url(self) -> str:
        return f"https://www.linkedin.com/feed/update/{self.id}/"


@dataclass
class QueuedPost:
    id: str
    commentary: str
    scheduled_at: str
    status: str = QUEUE_STATUS_PENDING
    image_path: str | None = None
    alt_text: str | None = None
    visibility: str = VISIBILITY_PUBLIC
    post_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "commentary": self.commentary,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "image_path": self.image_path,
            "alt_text": self.alt_text,
            "visibility": self.visibility,
            "post_id": self.post_id,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueuedPost":
        return cls(
            id=data["id"],
            commentary=data["commentary"],
            scheduled_at=data["scheduled_at"],
            status=data.get("status", QUEUE_STATUS_PENDING),
            image_path=data.get("image_path"),
            alt_text=data.get("alt_text"),
            visibility=data.get("visibility", VISIBILITY_PUBLIC),
            post_id=data.get("post_id"),
            error=data.get("error"),
        )


@dataclass
class MediaAsset:
    image_urn: str
    upload_url: str
    expires_at: int | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "MediaAsset":
        value = data.get("value") or {}
        return cls(
            image_urn=value.get("image", ""),
            upload_url=value.get("uploadUrl", ""),
            expires_at=value.get("uploadUrlExpiresAt"),
        )


@dataclass
class AuthToken:
    access_token: str
    refresh_token: str | None = None
    expires_in: int = 0
    obtained_at: int = 0

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "AuthToken":
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "obtained_at": self.obtained_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthToken":
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in", 0),
            obtained_at=data.get("obtained_at", 0),
        )

    def is_expired(self, now: int | None = None) -> bool:
        if self.expires_in <= 0:
            return False
        now = now or int(time.time())
        return now >= self.obtained_at + self.expires_in
