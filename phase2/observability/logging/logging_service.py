"""
phase2.observability.logging.logging_service
=============================================
Concrete ILoggingService implementation.

Logging destination (console / file / JSON format) is fully controlled
by ObservabilitySettings — no paths or levels are hardcoded.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Any, Optional

from phase2.observability.interfaces.observability_interface import ILoggingService
from phase2.observability.logging.json_formatter import JsonFormatter


class LoggingService(ILoggingService):
    """
    Emits structured log entries using Python's standard `logging` module.

    Two handlers are optionally configured:
      - StreamHandler  (console)    controlled by settings.log_to_console
      - RotatingFileHandler (file)  controlled by settings.log_to_file
    Both handlers use JsonFormatter when settings.log_format == "json".
    """

    def __init__(
        self,
        log_level: str,
        log_dir: str,
        log_to_file: bool,
        log_to_console: bool,
        log_format: str,
    ) -> None:
        self._logger = logging.getLogger("phase2.observability")
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        self._logger.setLevel(numeric_level)

        formatter: logging.Formatter
        if log_format.lower() == "json":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )

        if log_to_console and not self._has_handler(logging.StreamHandler):
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self._logger.addHandler(ch)

        if log_to_file:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            fh = logging.handlers.RotatingFileHandler(
                log_path / "observability.log",
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
            fh.setFormatter(formatter)
            if not self._has_handler(logging.handlers.RotatingFileHandler):
                self._logger.addHandler(fh)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _has_handler(self, handler_type: type) -> bool:
        return any(isinstance(h, handler_type) for h in self._logger.handlers)

    def _make_extra(self, execution_id: Optional[str], kwargs: dict) -> dict:
        extra: dict = {}
        if execution_id:
            extra["execution_id"] = execution_id
        extra.update(kwargs)
        return extra

    # ------------------------------------------------------------------
    # ILoggingService implementation
    # ------------------------------------------------------------------

    def log_info(self, message: str, execution_id: Optional[str] = None, **kwargs: Any) -> None:
        self._logger.info(message, extra=self._make_extra(execution_id, kwargs))

    def log_warning(self, message: str, execution_id: Optional[str] = None, **kwargs: Any) -> None:
        self._logger.warning(message, extra=self._make_extra(execution_id, kwargs))

    def log_error(self, message: str, execution_id: Optional[str] = None, **kwargs: Any) -> None:
        self._logger.error(message, extra=self._make_extra(execution_id, kwargs))

    def log_debug(self, message: str, execution_id: Optional[str] = None, **kwargs: Any) -> None:
        self._logger.debug(message, extra=self._make_extra(execution_id, kwargs))
