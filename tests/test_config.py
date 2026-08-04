import json

from linkedin_cli import config as config_module
from linkedin_cli.config import Config, load_config, save_config


def test_load_config_defaults(data_dir, monkeypatch):
    monkeypatch.delenv("LINKEDIN_CLI_CLIENT_ID", raising=False)
    monkeypatch.delenv("LINKEDIN_CLI_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("LINKEDIN_CLI_LANGUAGE", raising=False)
    monkeypatch.delenv("LINKEDIN_CLI_LOG_DAYS", raising=False)
    monkeypatch.delenv("LINKEDIN_CLI_API_VERSION", raising=False)
    monkeypatch.delenv("LINKEDIN_CLI_REQUEST_TIMEOUT", raising=False)
    monkeypatch.delenv("LINKEDIN_CLI_REDIRECT_URI", raising=False)

    cfg = load_config()

    assert cfg.client_id is None
    assert cfg.client_secret is None
    assert cfg.redirect_uri == "http://localhost:8080"
    assert cfg.api_version == "202604"
    assert cfg.language == "en"
    assert cfg.log_days == 120
    assert cfg.request_timeout == 60


def test_load_config_from_file(data_dir, monkeypatch):
    (data_dir / "config.json").write_text(
        json.dumps(
            {
                "client_id": "abc",
                "client_secret": "secret",
                "api_version": "202601",
                "language": "pt",
                "log_days": 30,
                "request_timeout": 15,
                "redirect_uri": "http://localhost:9999",
            }
        )
    )
    monkeypatch.delenv("LINKEDIN_CLI_LANGUAGE", raising=False)

    cfg = load_config()

    assert cfg.client_id == "abc"
    assert cfg.client_secret == "secret"
    assert cfg.api_version == "202601"
    assert cfg.language == "pt"
    assert cfg.log_days == 30
    assert cfg.request_timeout == 15
    assert cfg.redirect_uri == "http://localhost:9999"


def test_load_config_corrupted_file(data_dir, monkeypatch):
    (data_dir / "config.json").write_text("{not json")

    cfg = load_config()

    assert cfg.language == "en"
    assert cfg.log_days == 120


def test_load_config_env_overrides_file(data_dir, monkeypatch):
    (data_dir / "config.json").write_text(json.dumps({"client_id": "from_file", "log_days": 30}))
    monkeypatch.setenv("LINKEDIN_CLI_CLIENT_ID", "from_env")
    monkeypatch.setenv("LINKEDIN_CLI_LANGUAGE", "pt")
    monkeypatch.setenv("LINKEDIN_CLI_LOG_DAYS", "7")

    cfg = load_config()

    assert cfg.client_id == "from_env"
    assert cfg.language == "pt"
    assert cfg.log_days == 7


def test_load_config_invalid_language_env_falls_back(data_dir, monkeypatch):
    monkeypatch.setenv("LINKEDIN_CLI_LANGUAGE", "fr")

    cfg = load_config()

    assert cfg.language == "en"


def test_load_config_invalid_language_file_falls_back(data_dir, monkeypatch):
    (data_dir / "config.json").write_text(json.dumps({"language": "de"}))
    monkeypatch.delenv("LINKEDIN_CLI_LANGUAGE", raising=False)

    cfg = load_config()

    assert cfg.language == "en"


def test_load_config_invalid_int_env_falls_back_to_default(data_dir, monkeypatch):
    (data_dir / "config.json").write_text(json.dumps({"log_days": "not-an-int"}))

    cfg = load_config()

    assert cfg.log_days == 120


def test_save_config_writes_file(data_dir):
    save_config(
        Config(
            client_id="abc",
            client_secret="sec",
            language="pt",
            log_days=30,
            request_timeout=15,
            redirect_uri="http://localhost:1234",
            api_version="202603",
        )
    )

    saved = json.loads((data_dir / "config.json").read_text())
    assert saved == {
        "client_id": "abc",
        "client_secret": "sec",
        "language": "pt",
        "log_days": 30,
        "request_timeout": 15,
        "redirect_uri": "http://localhost:1234",
        "api_version": "202603",
    }


def test_save_config_filters_falsy_values(data_dir):
    save_config(Config())

    saved = json.loads((data_dir / "config.json").read_text())
    assert "client_id" not in saved
    assert "client_secret" not in saved
    assert saved["language"] == "en"


def test_normalize_language_helpers():
    assert config_module._normalize_language("pt") == "pt"
    assert config_module._normalize_language("en") == "en"
    assert config_module._normalize_language("xx") == "en"
    assert config_module._normalize_language(None) == "en"
