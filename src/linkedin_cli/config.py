import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_LANGUAGES = ("en", "pt")
DEFAULT_LANGUAGE = "en"

DATA_DIR = Path.home() / ".linkedin-cli"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"


@dataclass
class Config:
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str = "http://localhost:8080"
    api_version: str = "202604"
    language: str = DEFAULT_LANGUAGE
    log_days: int = 120
    request_timeout: int = 60


def _normalize_language(value: str | None) -> str:
    if value in SUPPORTED_LANGUAGES:
        return value
    return DEFAULT_LANGUAGE


def _to_int(value: object, default: int) -> int:
    if value is None:
        return default
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _load_config_file() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_config_file(data: dict[str, Any]) -> None:
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def load_config() -> Config:
    file_cfg = _load_config_file()
    return Config(
        client_id=os.environ.get("LINKEDIN_CLI_CLIENT_ID") or file_cfg.get("client_id"),
        client_secret=os.environ.get("LINKEDIN_CLI_CLIENT_SECRET") or file_cfg.get("client_secret"),
        redirect_uri=os.environ.get("LINKEDIN_CLI_REDIRECT_URI")
        or file_cfg.get("redirect_uri")
        or "http://localhost:8080",
        api_version=os.environ.get("LINKEDIN_CLI_API_VERSION")
        or file_cfg.get("api_version")
        or "202604",
        language=_normalize_language(
            os.environ.get("LINKEDIN_CLI_LANGUAGE") or file_cfg.get("language")
        ),
        log_days=_to_int(os.environ.get("LINKEDIN_CLI_LOG_DAYS") or file_cfg.get("log_days"), 120),
        request_timeout=_to_int(
            os.environ.get("LINKEDIN_CLI_REQUEST_TIMEOUT") or file_cfg.get("request_timeout"),
            60,
        ),
    )


def save_config(cfg: Config) -> None:
    data = {
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "redirect_uri": cfg.redirect_uri,
        "api_version": cfg.api_version,
        "language": cfg.language,
        "log_days": cfg.log_days,
        "request_timeout": cfg.request_timeout,
    }
    _save_config_file({k: v for k, v in data.items() if v})
