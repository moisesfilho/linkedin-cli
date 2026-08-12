import logging
import mimetypes
from typing import Any
from urllib.parse import quote

import requests as req_lib

from .auth import AuthService
from .config import load_config
from .formatter import escape_little_text
from .i18n import t
from .models import MediaAsset, Post

logger = logging.getLogger(__name__)

API_BASE = "https://api.linkedin.com"
POSTS_PATH = "/rest/posts"
IMAGES_PATH = "/rest/images"


class LinkedInError(Exception):
    pass


def _msg(msg_key: str, **kwargs: object) -> str:
    return t(load_config().language, msg_key=msg_key, **kwargs)


class LinkedInClient:
    def __init__(
        self,
        auth: AuthService | None = None,
        api_version: str | None = None,
        request_timeout: int | None = None,
    ) -> None:
        cfg = load_config()
        self.auth = auth or AuthService()
        self.api_version = api_version or cfg.api_version
        self.request_timeout = request_timeout or cfg.request_timeout
        self._session = req_lib.Session()

    def get_person_urn(self) -> str:
        return self.auth.get_person_urn()

    def create_post(
        self,
        commentary: str,
        visibility: str = "PUBLIC",
        image_urn: str | None = None,
        alt_text: str | None = None,
        escape_reserved: bool = True,
    ) -> Post:
        if escape_reserved:
            commentary = escape_little_text(commentary)
        body: dict[str, Any] = {
            "author": self.get_person_urn(),
            "commentary": commentary,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if image_urn:
            media: dict[str, Any] = {"id": image_urn}
            if alt_text:
                media["altText"] = alt_text
            body["content"] = {"media": media}
        resp = self._request(
            "POST",
            f"{API_BASE}{POSTS_PATH}",
            json=body,
            headers=self._headers(content_type=True),
        )
        if resp.status_code != 201:
            self._raise_for_status(resp)
        post_id = resp.headers.get("x-restli-id")
        if not post_id:
            raise LinkedInError(_msg("error_missing_id"))
        return Post(
            id=post_id,
            commentary=commentary,
            visibility=visibility,
            media_id=image_urn,
        )

    def upload_image(self, image_path: str) -> MediaAsset:
        person_urn = self.get_person_urn()
        init_body = {"initializeUploadRequest": {"owner": person_urn}}
        resp = self._request(
            "POST",
            f"{API_BASE}{IMAGES_PATH}?action=initializeUpload",
            json=init_body,
            headers=self._headers(content_type=True),
        )
        if resp.status_code != 200:
            self._raise_for_status(resp)
        asset = MediaAsset.from_response(resp.json())
        if not asset.upload_url or not asset.image_urn:
            raise LinkedInError(_msg("error_missing_upload"))
        content_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
        try:
            with open(image_path, "rb") as f:
                upload = self._request(
                    "PUT",
                    asset.upload_url,
                    data=f,
                    headers={"Content-Type": content_type},
                )
        except OSError:
            raise LinkedInError(_msg("error_read_image", path=image_path))
        if upload.status_code not in (200, 201):
            self._raise_for_status(upload)
        return asset

    def list_posts(self, max_count: int = 10) -> list[Post]:
        person_urn = self.get_person_urn()
        params: dict[str, Any] = {
            "author": person_urn,
            "q": "author",
            "count": max_count,
            "sortBy": "CREATED",
        }
        headers = self._headers()
        headers["X-RestLi-Method"] = "FINDER"
        resp = self._request("GET", f"{API_BASE}{POSTS_PATH}", params=params, headers=headers)
        if resp.status_code == 403:
            raise LinkedInError(_msg("post_list_requires_scope"))
        if resp.status_code != 200:
            self._raise_for_status(resp)
        posts: list[Post] = []
        for elem in resp.json().get("elements", []):
            posts.append(
                Post(
                    id=elem.get("id", ""),
                    commentary=elem.get("commentary", ""),
                    visibility=elem.get("visibility", "PUBLIC"),
                    published_at=elem.get("publishedAt"),
                    media_id=elem.get("content", {}).get("media", {}).get("id"),
                    lifecycle_state=elem.get("lifecycleState", "PUBLISHED"),
                )
            )
        return posts

    def get_post(self, post_id: str) -> Post:
        resp = self._request(
            "GET",
            f"{API_BASE}{POSTS_PATH}/{quote(post_id, safe='')}",
            headers=self._headers(),
        )
        if resp.status_code != 200:
            self._raise_for_status(resp)
        data = resp.json()
        return Post(
            id=data.get("id", post_id),
            commentary=data.get("commentary", ""),
            visibility=data.get("visibility", "PUBLIC"),
            published_at=data.get("publishedAt"),
            media_id=data.get("content", {}).get("media", {}).get("id"),
            lifecycle_state=data.get("lifecycleState", "PUBLISHED"),
        )

    def delete_post(self, post_id: str) -> None:
        headers = self._headers()
        headers["X-RestLi-Method"] = "DELETE"
        resp = self._request(
            "DELETE",
            f"{API_BASE}{POSTS_PATH}/{quote(post_id, safe='')}",
            headers=headers,
        )
        if resp.status_code != 204:
            self._raise_for_status(resp)

    def _headers(self, *, content_type: bool = False) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.auth.get_token().access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        if content_type:
            headers["Content-Type"] = "application/json"
        return headers

    def _request(self, method: str, url: str, **kwargs: Any) -> req_lib.Response:
        try:
            return self._session.request(
                method,
                url,
                timeout=(self.request_timeout, self.request_timeout),
                **kwargs,
            )
        except req_lib.RequestException as exc:
            raise LinkedInError(_msg("error_generic", message=str(exc))) from exc

    def _raise_for_status(self, resp: req_lib.Response) -> None:
        code = resp.status_code
        try:
            message: str = str(resp.json().get("message") or resp.text)
        except ValueError:
            message = resp.text
        if code == 401:
            raise LinkedInError(_msg("error_unauthorized"))
        if code == 403:
            raise LinkedInError(_msg("error_permission"))
        if code == 404:
            raise LinkedInError(_msg("error_not_found", resource=str(resp.url)))
        if code == 429:
            raise LinkedInError(_msg("error_rate_limited"))
        if 400 <= code < 500:
            raise LinkedInError(_msg("error_invalid_request", message=message))
        raise LinkedInError(_msg("error_server", code=code))
