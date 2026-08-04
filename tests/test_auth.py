import json
import socket
import threading
import time

import pytest
import requests as req_lib
from conftest import FakeResponse

import linkedin_cli.auth as auth_module
from linkedin_cli.auth import AuthError, AuthService, CredentialsNotFoundError
from linkedin_cli.models import AuthToken


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _fresh_token(**kwargs) -> AuthToken:
    defaults = {
        "access_token": "acc",
        "refresh_token": "ref",
        "expires_in": 3600,
        "obtained_at": int(time.time()),
    }
    defaults.update(kwargs)
    return AuthToken(**defaults)


@pytest.fixture
def service(data_dir):
    (data_dir / "config.json").write_text(
        json.dumps(
            {
                "client_id": "cid",
                "client_secret": "csec",
                "redirect_uri": "http://localhost:8080",
            }
        )
    )
    return AuthService()


def test_build_authorization_url(service):
    url = service.build_authorization_url("state123")
    assert url.startswith("https://www.linkedin.com/oauth/v2/authorization?")
    assert "response_type=code" in url
    assert "client_id=cid" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080" in url
    assert "scope=openid+profile+email+w_member_social" in url
    assert "state=state123" in url


def test_login_requires_credentials(data_dir):
    with pytest.raises(AuthError):
        AuthService().login()


def test_login_full_flow(service, data_dir, mocker):
    mocker.patch.object(service, "_run_local_callback", return_value="the-code")
    mocker.patch.object(
        service,
        "_exchange_code",
        return_value=AuthToken(access_token="acc", refresh_token="ref", expires_in=3600),
    )

    token = service.login()

    assert token.access_token == "acc"
    saved = json.loads((data_dir / "token.json").read_text())
    assert saved["access_token"] == "acc"
    assert saved["obtained_at"] == token.obtained_at


def test_run_local_callback_success(service, mocker):
    port = _free_port()
    mocker.patch.object(service, "_callback_address", return_value=("127.0.0.1", port))
    mocker.patch.object(
        auth_module.webbrowser,
        "open",
        side_effect=lambda _url: threading.Thread(
            target=_get, args=(f"http://127.0.0.1:{port}/?state=st&code=good-code",)
        ).start(),
    )

    code = service._run_local_callback("https://auth.example?state=st", "st")

    assert code == "good-code"


def test_run_local_callback_reports_error(service, mocker):
    port = _free_port()
    mocker.patch.object(service, "_callback_address", return_value=("127.0.0.1", port))
    mocker.patch.object(
        auth_module.webbrowser,
        "open",
        side_effect=lambda _url: threading.Thread(
            target=_get, args=(f"http://127.0.0.1:{port}/?error=access_denied",)
        ).start(),
    )

    with pytest.raises(AuthError):
        service._run_local_callback("https://auth.example", "st")


def test_run_local_callback_timeout(service, mocker, monkeypatch):
    port = _free_port()
    monkeypatch.setattr(auth_module, "CALLBACK_TIMEOUT", 0.1)
    mocker.patch.object(service, "_callback_address", return_value=("127.0.0.1", port))
    mocker.patch.object(auth_module.webbrowser, "open", side_effect=lambda _url: None)

    with pytest.raises(AuthError):
        service._run_local_callback("https://auth.example", "st")


def test_run_local_callback_no_code(service, mocker):
    port = _free_port()
    mocker.patch.object(service, "_callback_address", return_value=("127.0.0.1", port))
    mocker.patch.object(
        auth_module.webbrowser,
        "open",
        side_effect=lambda _url: threading.Thread(
            target=_get, args=(f"http://127.0.0.1:{port}/?state=st",)
        ).start(),
    )

    with pytest.raises(AuthError):
        service._run_local_callback("https://auth.example", "st")


def test_callback_address_parses_uri():
    service = AuthService(redirect_uri="https://example.com:9999/callback")
    assert service._callback_address() == ("example.com", 9999)


def test_callback_address_default_port():
    service = AuthService(redirect_uri="http://localhost/callback")
    assert service._callback_address() == ("localhost", 8080)


def test_save_token_cleans_temp_on_failure(service, data_dir, mocker):
    mocker.patch("linkedin_cli.auth.json.dump", side_effect=OSError("disk full"))

    with pytest.raises(OSError, match="disk full"):
        service._save_token(_fresh_token())

    assert list(data_dir.glob("token.*.tmp")) == []


def _get(url: str) -> None:
    req_lib.get(url, timeout=5)


def test_oauth_callback_handle():
    cb = auth_module._OAuthCallback("expected")
    cb.handle({"state": ["expected"], "code": ["c1"]})
    assert cb.code == "c1"
    assert cb.error is None
    assert cb.ready.is_set()


def test_oauth_callback_error():
    cb = auth_module._OAuthCallback("expected")
    cb.handle({"error": ["access_denied"]})
    assert cb.error == "access_denied"
    assert cb.code is None
    assert cb.ready.is_set()


def test_oauth_callback_state_mismatch():
    cb = auth_module._OAuthCallback("expected")
    cb.handle({"state": ["other"], "code": ["c1"]})
    assert cb.error == "state_mismatch"
    assert cb.code is None


def test_exchange_code(service, mocker):
    resp = FakeResponse(200, {"access_token": "acc", "refresh_token": "ref", "expires_in": 5184000})
    mocker.patch.object(service._session, "post", return_value=resp)

    token = service._exchange_code("code")

    assert token.access_token == "acc"
    assert token.refresh_token == "ref"
    assert token.expires_in == 5184000


def test_exchange_code_accepts_missing_refresh(service, mocker):
    resp = FakeResponse(200, {"access_token": "acc"})
    mocker.patch.object(service._session, "post", return_value=resp)

    token = service._exchange_code("code")

    assert token.access_token == "acc"
    assert token.refresh_token is None


def test_exchange_code_empty_token_raises(service, mocker):
    resp = FakeResponse(200, {"foo": "bar"})
    mocker.patch.object(service._session, "post", return_value=resp)
    with pytest.raises(AuthError):
        service._exchange_code("code")


def test_get_token_no_file(service):
    with pytest.raises(CredentialsNotFoundError):
        service.get_token()


def test_get_token_valid(service):
    service._save_token(_fresh_token())

    token = service.get_token()

    assert token.access_token == "acc"


def test_get_token_expired_refreshes_and_saves(service, data_dir, mocker):
    service._save_token(
        AuthToken(access_token="old", refresh_token="ref", expires_in=10, obtained_at=0)
    )
    fresh = AuthToken(access_token="new", refresh_token="newref", expires_in=3600, obtained_at=500)
    mocker.patch.object(service, "_refresh_token", return_value=fresh)

    token = service.get_token()

    assert token.access_token == "new"
    assert json.loads((data_dir / "token.json").read_text())["access_token"] == "new"


def test_refresh_token(service, mocker):
    resp = FakeResponse(
        200, {"access_token": "newacc", "refresh_token": "newref", "expires_in": 3600}
    )
    mocker.patch.object(service._session, "post", return_value=resp)

    token = service._refresh_token(AuthToken(access_token="old", refresh_token="ref"))

    assert token.access_token == "newacc"
    assert token.refresh_token == "newref"
    assert token.obtained_at > 0


def test_refresh_token_keeps_old_refresh(service, mocker):
    resp = FakeResponse(200, {"access_token": "newacc"})
    mocker.patch.object(service._session, "post", return_value=resp)

    token = service._refresh_token(AuthToken(access_token="old", refresh_token="ref"))

    assert token.refresh_token == "ref"


def test_refresh_token_missing_refresh_raises(service):
    with pytest.raises(AuthError):
        service._refresh_token(AuthToken(access_token="old"))


def test_refresh_token_empty_access_raises(service, mocker):
    resp = FakeResponse(200, {"foo": "bar"})
    mocker.patch.object(service._session, "post", return_value=resp)
    with pytest.raises(AuthError):
        service._refresh_token(AuthToken(access_token="old", refresh_token="ref"))


def test_get_person_urn(service, mocker):
    service._save_token(_fresh_token())
    resp = FakeResponse(200, {"sub": "abc123"})
    mocker.patch.object(service._session, "get", return_value=resp)

    urn = service.get_person_urn()

    assert urn == "urn:li:person:abc123"
    assert service._person_urn == urn


def test_get_person_urn_cached(service, mocker):
    service._person_urn = "urn:li:person:123"
    assert service.get_person_urn() == "urn:li:person:123"


def test_get_person_urn_missing_sub(service, mocker):
    service._save_token(_fresh_token())
    resp = FakeResponse(200, {"name": "x"})
    mocker.patch.object(service._session, "get", return_value=resp)
    with pytest.raises(AuthError):
        service.get_person_urn()


def test_is_authenticated(service):
    assert service.is_authenticated() is False
    service._save_token(_fresh_token())
    assert service.is_authenticated() is True


def test_is_authenticated_expired(service):
    service._save_token(
        AuthToken(access_token="acc", refresh_token="ref", expires_in=10, obtained_at=0)
    )
    assert service.is_authenticated() is False


def test_logout_removes_token(service, data_dir):
    service._save_token(_fresh_token())
    service.logout()
    assert not (data_dir / "token.json").exists()
    service.logout()


def test_load_token_corrupted(service, data_dir):
    (data_dir / "token.json").write_text("{broken")
    assert service._load_token() is None
