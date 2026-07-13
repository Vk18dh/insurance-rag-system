"""
phase2.logging.logger
======================

Structured logging infrastructure for Phase 2 – Agentic RAG System.

Features:
    - JSON-formatted log records (compatible with ELK, Datadog, CloudWatch)
    - Text format fallback for development readability
    - Rotating file handler (max_bytes and backup_count from configuration)
    - Per-agent named loggers via get_logger()
    - No PII/query content logged beyond the configurable preview length
    - All log settings loaded from Phase2Settings — nothing hardcoded

Usage::

    from phase2.logging.logger import get_logger, setup_phase2_logging
    from phase2.config import get_settings

    setup_phase2_logging(get_settings())         # called once at startup
    logger = get_logger(__name__)                 # in every module
    logger.info("Agent started", extra={"agent": "QueryUnderstandingAgent"})

Structured JSON record example::

    {
      "timestamp": "2026-07-13T12:34:56.789Z",
      "level": "INFO",
      "logger": "phase2.agents.query_agent",
      "message": "Query processing complete",
      "query_id": "abc-123",
      "agent": "QueryUnderstandingAgent",
      "elapsed_ms": 42.1
    }
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ===========================================================================
# JSON formatter
# ===========================================================================

class JsonFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Every record includes:
        - timestamp   : ISO-8601 UTC
        - level       : log level name
        - logger      : logger hierarchy name
        - message     : formatted log message
        - module      : source module name
        - lineno      : source line number
        - exc_info    : exception traceback (if present)

    Any extra fields passed via `extra={}` or `logging.LogRecord` attributes
    are merged into the root JSON object.

    Args:
        reserved_attrs: Set of LogRecord attribute names to exclude from
                        the extra-fields merge (prevents duplication).
    """

    _RESERVED: frozenset[str] = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        """
        Serialise a LogRecord to a single-line JSON string.

        Args:
            record: The log record to format.

        Returns:
            str: JSON-encoded log line.
        """
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "lineno": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_obj["stack_info"] = self.formatStack(record.stack_info)

        # Merge extra fields (e.g. query_id, agent, elapsed_ms)
        for key, val in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                log_obj[key] = val

        try:
            return json.dumps(log_obj, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            # Fallback: never let the formatter crash the application
            safe = {k: str(v) for k, v in log_obj.items()}
            return json.dumps(safe, ensure_ascii=False)


# ===========================================================================
# Text formatter (for development)
# ===========================================================================

class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development environments.

    Format: TIMESTAMP | LEVEL    | LOGGER_NAME | message [key=value ...]
    """

    _FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    _DATE_FMT = "%Y-%m-%dT%H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self._FMT, datefmt=self._DATE_FMT)


# ===========================================================================
# Logging setup
# ===========================================================================

_SETUP_LOCK: threading.Lock = threading.Lock()  # Guards _SETUP_DONE in multi-threaded envs
_SETUP_DONE: bool = False


def setup_phase2_logging(settings: Any) -> None:
    """
    Configure the Phase 2 logging subsystem from settings.

    Must be called once at application startup before any log statements
    are emitted. Safe to call multiple times (idempotent).

    Handlers configured:
        - StreamHandler (stdout) — always enabled
        - RotatingFileHandler    — enabled when settings.logging.log_dir is set

    Args:
        settings: Phase2Settings instance (phase2.config.settings).
                  All values come from configuration — nothing is hardcoded.

    Side effects:
        - Configures the root 'phase2' logger and all child loggers.
        - Creates the log directory if it does not exist.
    """
    global _SETUP_DONE
    with _SETUP_LOCK:
        if _SETUP_DONE:
            return
        _do_setup(settings)
        _SETUP_DONE = True


def _do_setup(settings: Any) -> None:
    """Internal: perform the actual logging configuration (called under lock)."""
    log_cfg = settings.logging
    level = getattr(logging, log_cfg.level.upper(), logging.INFO)
    use_json = log_cfg.format.lower() == "json"

    formatter: logging.Formatter = JsonFormatter() if use_json else TextFormatter()

    # ── Root phase2 logger ────────────────────────────────────────────────
    root_logger = logging.getLogger("phase2")
    root_logger.setLevel(level)
    root_logger.propagate = False  # Don't bubble to root logger

    # ── Console handler ───────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ── Rotating file handler ─────────────────────────────────────────────
    try:
        log_dir = Path(log_cfg.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / log_cfg.log_filename

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=log_cfg.max_bytes,
            backupCount=log_cfg.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        root_logger.info(
            "Phase 2 file logging enabled",
            extra={"log_file": str(log_file), "max_bytes": log_cfg.max_bytes},
        )
    except OSError as exc:
        root_logger.warning(
            "Could not initialise file logging: %s — console only.", exc
        )

    root_logger.info(
        "Phase 2 logging initialised",
        extra={
            "level": log_cfg.level,
            "format": log_cfg.format,
            "environment": getattr(settings, "environment", "unknown"),
        },
    )


def reset_logging() -> None:
    """
    Reset the logging setup guard.

    Intended for use in tests that need to reconfigure logging between runs.
    Should NOT be called in production code.
    """
    global _SETUP_DONE
    with _SETUP_LOCK:
        _SETUP_DONE = False
        root_logger = logging.getLogger("phase2")
        root_logger.handlers.clear()


# ===========================================================================
# Logger factory
# ===========================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Return a named child logger under the 'phase2' hierarchy.

    All phase2 loggers share the root 'phase2' configuration set by
    setup_phase2_logging(). If called before setup, logs will still work
    (Python's logging is lazy) but may use default formatting.

    Args:
        name: Typically __name__ of the calling module.
              e.g. 'phase2.agents.query_agent' → logger name 'phase2.agents.query_agent'

    Returns:
        logging.Logger: Named child logger.

    Example::

        logger = get_logger(__name__)
        logger.info("Processing query", extra={"query_id": "abc-123"})
    """
    # Ensure name is rooted under 'phase2' so it inherits root config
    if not name.startswith("phase2"):
        name = f"phase2.{name}"
    return logging.getLogger(name)


# ===========================================================================
# Audit log helper
# ===========================================================================

def log_query_audit(
    logger: logging.Logger,
    event: str,
    query_id: Optional[str],
    agent_name: str,
    elapsed_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Emit a structured audit log entry for a query lifecycle event.

    All audit events include query_id for correlation.
    This function is the single place where audit log structure is defined,
    ensuring consistent field names across all agents.

    Args:
        logger    : The calling module's logger.
        event     : Short event name (e.g. 'query_received', 'intent_detected').
        query_id  : UUID from QueryMetadata (may be None if metadata not yet set).
        agent_name: Name of the agent emitting the event.
        elapsed_ms: Optional processing time in milliseconds.
        extra     : Additional key-value pairs to include in the log record.
    """
    fields: Dict[str, Any] = {
        "event": event,
        "query_id": query_id or "unknown",
        "agent": agent_name,
    }
    if elapsed_ms is not None:
        fields["elapsed_ms"] = round(elapsed_ms, 2)
    if extra:
        fields.update(extra)

    logger.info("AUDIT | %s", event, extra=fields)
