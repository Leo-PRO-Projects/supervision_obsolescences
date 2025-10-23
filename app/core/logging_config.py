from __future__ import annotations

import logging
import sys
from logging.config import dictConfig

from .config import get_settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        log_entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        return self.jsonify(log_entry)

    @staticmethod
    def jsonify(data: dict) -> str:
        try:
            import json

            return json.dumps(data, ensure_ascii=False)
        except Exception:  # pragma: no cover - fallback to str
            return str(data)


def configure_logging() -> None:
    settings = get_settings()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                }
            },
            "handlers": {
                "default": {
                    "level": settings.log_level,
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "json",
                }
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["default"],
            },
        }
    )
