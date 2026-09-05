"""
Structured JSON & Contextual Logging System
"""
import json
import logging
import sys
from datetime import datetime, timezone
from backend.app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Format logs as structured JSON objects for ingestion by observability stacks
    """
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
        }

        if hasattr(record, "request_id"):
            log_object["request_id"] = record.request_id

        if hasattr(record, "video_id"):
            log_object["video_id"] = record.video_id

        if hasattr(record, "incident_id"):
            log_object["incident_id"] = record.incident_id

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_object)


def setup_logging():
    """Configure system-wide logging with JSON and console streams"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Mute noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


logger = logging.getLogger("guardian_eye")
