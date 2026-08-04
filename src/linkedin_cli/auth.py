import contextlib
import json
import logging
import os
import secrets
import tempfile
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests as req_lib

from .config import DATA_DIR, load_config
from .i18n import t
from .models import AuthToken

logger = logging.getLogger(__name__)

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

SCOPES = "openid profile email w_member_social"

CALLBACK_TIMEOUT = 600


class AuthError(Exception):
    pass


class CredentialsNotFoundError(AuthError):
    pass


def _msg(msg_key: str, **kwargs: object) -> str:
    return t(load_config().language, msg_key=msg_key, **kwargs)


class _OAuthCallback:
    def __init__(self, expected_state: str) -> None:
        self.expected_state = expected_state
        self.code: str | None = None
        self.error: str | None = None
        self.ready = threading.Event()

    def handle(self, query: dict[str, list[str]]) -> None:
        if query.get("error"):
            self.error = query["error"][0]
        elif query.get("state") == [self.expected_state]:
            self.code = query.get("code", [None])[0]
        else:
            self.error = "state_mismatch"
        self.ready.set()


class _CallbackHandler(BaseHTTPRequestHandler):
    callback: _OAuthCallback = None  # type: ignore[assignment]

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        self.callback.handle(query)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Authorization complete</h1>"
            b"<p>You can close this window and return to the terminal.</p></body></html>"
        )

    def log_message(self, format: str, *args: object) -> None:
        return


class AuthService:
    TOKEN_FILE: Path = DATA_DIR / "token.json"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        request_timeout: int | None = None,
    ) -> None:
        cfg = load_config()
        self.client_id = client_id or cfg.client_id
        self.client_secret = client_secret or cfg.client_secret
        self.redirect_uri = redirect_uri or cfg.redirect_uri
        self.request_timeout = request_timeout or cfg.request_timeout
        self._person_urn: str | None = None
        self._session = req_lib.Session()

    def build_authorization_url(self, state: str) -> str:
        params = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id or "",
                "redirect_uri": self.redirect_uri,
                "scope": SCOPES,
                "state": state,
            }
        )
        return f"{AUTH_URL}?{params}"

    def login(self) -> AuthToken:
        if not self.client_id or not self.client_secret:
            raise AuthError(_msg("auth_login_guide"))
        state = secrets.token_urlsafe(16)
        auth_url = self.build_authorization_url(state)
        code = self._run_local_callback(auth_url, state)
        token = self._exchange_code(code)
        token.obtained_at = int(time.time())
        self._save_token(token)
        return token

    def _run_local_callback(self, auth_url: str, state: str) -> str:
        host, port = self._callback_address()
        callback = _OAuthCallback(state)
        _CallbackHandler.callback = callback

        server = HTTPServer((host, port), _CallbackHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        webbrowser.open(auth_url)
        try:
            if not callback.ready.wait(timeout=CALLBACK_TIMEOUT):
                raise AuthError(_msg("auth_callback_timeout"))
            if callback.error:
                raise AuthError(_msg("auth_callback_failed", reason=callback.error))
            if not callback.code:
                raise AuthError(_msg("auth_callback_failed", reason="no code"))
            return callback.code
        finally:
            server.shutdown()
            thread.join(timeout=2)

    def _callback_address(self) -> tuple[str, int]:
        parsed = urlparse(self.redirect_uri)
        return parsed.hostname or "127.0.0.1", parsed.port or 8080

    def _exchange_code(self, code: str) -> AuthToken:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id or "",
            "client_secret": self.client_secret or "",
            "redirect_uri": self.redirect_uri,
        }
        resp = self._session.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        payload = resp.json()
        token = AuthToken.from_response(payload)
        if not token.access_token:
            raise AuthError(_msg("auth_error", message=payload))
        if not token.refresh_token:
            logger.warning("no refresh_token returned; access token valid until expiry")
        return token

    def get_token(self) -> AuthToken:
        token = self._load_token()
        if token is None:
            raise CredentialsNotFoundError(_msg("auth_no_credentials"))
        if token.is_expired():
            token = self._refresh_token(token)
            self._save_token(token)
        return token

    def _refresh_token(self, token: AuthToken) -> AuthToken:
        if not token.refresh_token:
            raise AuthError(_msg("auth_token_expired"))
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "client_id": self.client_id or "",
            "client_secret": self.client_secret or "",
        }
        resp = self._session.post(
            TOKEN_URL, data=data, timeout=(self.request_timeout, self.request_timeout)
        )
        resp.raise_for_status()
        payload = resp.json()
        fresh = AuthToken.from_response(payload)
        if not fresh.access_token:
            raise AuthError(_msg("auth_token_expired"))
        fresh.obtained_at = int(time.time())
        if not fresh.refresh_token:
            fresh.refresh_token = token.refresh_token
        return fresh

    def get_person_urn(self) -> str:
        if self._person_urn is not None:
            return self._person_urn
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token.access_token}"}
        resp = self._session.get(
            USERINFO_URL, headers=headers, timeout=(self.request_timeout, self.request_timeout)
        )
        resp.raise_for_status()
        sub = resp.json().get("sub")
        if not sub:
            raise AuthError(_msg("auth_no_urn"))
        self._person_urn = f"urn:li:person:{sub}"
        return self._person_urn

    def is_authenticated(self) -> bool:
        token = self._load_token()
        return token is not None and not token.is_expired()

    def logout(self) -> None:
        with contextlib.suppress(OSError):
            self.TOKEN_FILE.unlink()

    def _load_token(self) -> AuthToken | None:
        if not self.TOKEN_FILE.exists():
            return None
        try:
            return AuthToken.from_dict(json.loads(self.TOKEN_FILE.read_text()))
        except (json.JSONDecodeError, OSError, TypeError):
            return None

    def _save_token(self, token: AuthToken) -> None:
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.TOKEN_FILE.parent), prefix="token.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(token.to_dict(), f)
            os.replace(tmp_path, str(self.TOKEN_FILE))
        except BaseException:
            with contextlib.suppress(OSError):
                Path(tmp_path).unlink()
            raise
