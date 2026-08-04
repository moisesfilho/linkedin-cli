import logging
from logging.handlers import TimedRotatingFileHandler

from linkedin_cli import logging_utils
from linkedin_cli.config import Config
from linkedin_cli.logging_utils import get_logger


def test_get_logger_creates_file_handler(data_dir, clean_logger, mocker):
    logger = get_logger()

    assert logging_utils.LOG_FILE.parent.exists()
    assert logger.name == "linkedin_cli"
    assert any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers)


def test_get_logger_returns_same_instance(data_dir, clean_logger):
    first = get_logger()
    second = get_logger()

    assert first is second
    assert len(first.handlers) == 1


def test_get_logger_uses_explicit_log_days(data_dir, clean_logger, mocker):
    mocker.patch("linkedin_cli.logging_utils.load_config", return_value=Config(log_days=50))
    logger = get_logger(log_days=50)

    handler = next(h for h in logger.handlers if isinstance(h, TimedRotatingFileHandler))
    assert handler.backupCount == 50


def test_get_logger_uses_config_log_days(data_dir, clean_logger, mocker):
    mocker.patch("linkedin_cli.logging_utils.load_config", return_value=Config(log_days=30))
    logger = get_logger()

    handler = next(h for h in logger.handlers if isinstance(h, TimedRotatingFileHandler))
    assert handler.backupCount == 30


def test_get_logger_writes_log_entries(data_dir, clean_logger):
    logger = get_logger()
    logger.info("hello world")

    assert "hello world" in logging_utils.LOG_FILE.read_text()


def test_logger_propagate_disabled(data_dir, clean_logger):
    logger = get_logger()

    assert logger.propagate is False
    assert logger.level == logging.INFO
