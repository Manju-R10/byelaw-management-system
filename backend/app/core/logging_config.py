"""Centralized application logging configuration.

A single ``setup_logging()`` call configures the root logger with a consistent,
timestamped format. The log level is driven by ``settings.LOG_LEVEL`` so it can be
tuned per environment without code changes (NFR: Maintainability/Auditability).
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

# Backend directory: .../backend  (this file is .../backend/app/core/logging_config.py)
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_LOG_DIR = _BACKEND_DIR / "logs"

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging() -> None:
    """Configure root logging once. Safe to call multiple times (idempotent)."""
    global _configured
    if _configured:
        return

    level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root = logging.getLogger()
    root.setLevel(level)
    # Clear any pre-existing handlers (e.g. from uvicorn reload) to avoid duplicate lines.
    root.handlers.clear()

    # Console handler.
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)
    root.addHandler(console)

    # Rotating file handler — keeps an on-disk audit trail of application activity.
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            _LOG_DIR / "application.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB per file
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root.addHandler(file_handler)
    except OSError:
        # If the log directory cannot be created we still run with console logging.
        root.warning("Could not initialize file logging in %s; using console only.", _LOG_DIR)

    # Tame noisy third-party loggers in non-debug environments.
    if level > logging.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("aiomysql").setLevel(logging.WARNING)

    _configured = True
    root.info("Logging configured at level %s (env=%s).", logging.getLevelName(level), settings.ENV)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
