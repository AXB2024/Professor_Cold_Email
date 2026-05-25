import logging
import logging.config
from pathlib import Path

from app.core.config import Settings


def setup_logging(settings: Settings) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": settings.log_level,
            },
            "app_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "app.log"),
                "maxBytes": 2 * 1024 * 1024,
                "backupCount": 3,
                "formatter": "standard",
                "level": settings.log_level,
            },
            "sent_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "sent_emails.log"),
                "maxBytes": 2 * 1024 * 1024,
                "backupCount": 3,
                "formatter": "standard",
                "level": "INFO",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "app_file"],
                "level": settings.log_level,
            },
            "sent_email": {
                "handlers": ["console", "sent_file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(logging_config)

