import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


# ── Structured Log Processors ──/───

def add_log_level(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Add log level to structured log."""
    event_dict["level"] = method_name.upper()
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Add ISO timestamp."""
    from datetime import datetime
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def add_exc_info(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Add exception info if present."""
    if "exc_info" in event_dict and event_dict["exc_info"]:
        event_dict["exception"] = structlog.processors.format_exc_info(
            logger, method_name, event_dict
        )
    return event_dict


# ── Context Variables (for request/user correlation) ──────/---------

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar("user_id", default=None)


def add_request_context(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Inject request_id and user_id into logs if available."""
    if rid := request_id_var.get():
        event_dict["request_id"] = rid
    if uid := user_id_var.get():
        event_dict["user_id"] = uid
    return event_dict


# ── Configure structlog ────────────/────────────

def configure_logging() -> None:
    """Configure structlog and standard logging for the application."""
    processors = [
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        add_request_context,
    ]

    if settings.DEBUG:
        # Development: pretty colored console output
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )
        log_level = "DEBUG"
    else:
        # Production: JSON structured logs
        processors.extend(
            [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ]
        )
        log_level = "INFO"

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Also configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    logger.info("Logging configured", mode="development" if settings.DEBUG else "production")


# ── Middleware to inject request context ──────────/────────────

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set request_id and user_id in contextvars for logging."""

    async def dispatch(self, request: Request, call_next):
        # Generate or get request ID (you can also use correlation-id header)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        # Optional: set user_id if authenticated    
        
        user_id_var.set(None)  # Will be set in deps if authenticated

        response = await call_next(request)
        return response


# ── Public API ─────────────────────────────/────────────
# Get a logger instance anywhere in the app
def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Convenience exports
logger = get_logger("app")          # Default app logger
logger_db = get_logger("database")  # For DB-related logs
logger_ml = get_logger("inference") # For model/inference logs
logger_api = get_logger("api")      # For endpoint/request logs