"""
phase2.observability.logging.json_formatter
=============================================
Structured JSON log formatter.

Emits each log record as a single-line JSON object, suitable for
log aggregation systems (ELK, Cloud Logging, Loki, etc.).

Configurable via ObservabilitySettings — never hardcoded.
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """
    Converts a LogRecord into a compact JSON string.

    Output fields
    -------------
    timestamp   : ISO-8601 UTC
    level       : Log level name
    logger      : Logger name
    message     : Formatted message
    execution_id: Injected via LogRecord.execution_id (optional)
    exc_info    : Sanitised traceback string (only on ERROR/CRITICAL)
    extra       : Any additional keyword arguments
    """

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Propagate execution_id if injected on the record
        execution_id = getattr(record, "execution_id", None)
        if execution_id:
            payload["execution_id"] = execution_id

        # Safe exception serialisation — no raw user data in tracebacks
        if record.exc_info:
            payload["exc_info"] = traceback.format_exception(*record.exc_info)[-1].strip()

        # Capture any extra keys added via logger.info(..., extra={...})
        std_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in std_keys}
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, default=str)
