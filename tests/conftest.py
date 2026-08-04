import json
import logging

import pytest
import requests as req_lib

from linkedin_cli import config as config_module
from linkedin_cli import logging_utils
from linkedin_cli.auth import AuthService


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(logging_utils, "LOG_FILE", tmp_path / "logs" / "linkedin-cli.log")
    monkeypatch.setattr(AuthService, "TOKEN_FILE", tmp_path / "token.json")
    return tmp_path


@pytest.fixture
def clean_logger():
    yield
    logger = logging.getLogger(logging_utils._LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    del logging.Logger.manager.loggerDict[logging_utils._LOGGER_NAME]


class FakeResponse:
    def __init__(self, status_code, data=None, headers=None, text=""):
        self.status_code = status_code
        self._data = data
        self.headers = headers or {}
        self.text = text or (json.dumps(data) if data is not None else "")
        self.url = "https://api.linkedin.com/rest/posts"

    def json(self):
        if self._data is None:
            raise ValueError("No JSON body")
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise req_lib.HTTPError(f"{self.status_code} Client Error")
