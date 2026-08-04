import logging
from logging.handlers import TimedRotatingFileHandler

from .config import DATA_DIR, load_config

LOG_FILE = DATA_DIR / "logs" / "linkedin-cli.log"

_LOGGER_NAME = "linkedin_cli"


def get_logger(log_days: int | None = None) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        return logger
    if log_days is None:
        log_days = load_config().log_days
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="D",
        interval=1,
        backupCount=log_days,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    return logger
