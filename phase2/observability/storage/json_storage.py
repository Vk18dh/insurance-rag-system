"""
phase2.observability.storage.json_storage
==========================================
Append-only JSONL storage backend.

Each event type is written to a dated file in the configured audit_dir.
The directory is created on first write — no hardcoded paths.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from phase2.observability.interfaces.observability_interface import IStorageBackend
from phase2.observability.models.observability_event import AgentExecutionEvent
from phase2.observability.models.audit_record import AuditRecord
from phase2.observability.models.execution_metrics import ExecutionMetrics
from phase2.observability.models.alert_event import AlertEvent
from phase2.observability.exceptions import StorageException


class JsonStorageBackend(IStorageBackend):
    """
    Appends one JSON object per line to dated log files.

    File naming pattern (all in audit_dir):
        events_YYYY-MM-DD.jsonl
        audits_YYYY-MM-DD.jsonl
        metrics_YYYY-MM-DD.jsonl
        alerts_YYYY-MM-DD.jsonl

    Thread-safe via a per-file lock.
    """

    def __init__(self, audit_dir: str) -> None:
        self._audit_dir = Path(audit_dir)
        self._audit_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _dated_path(self, prefix: str) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self._audit_dir / f"{prefix}_{date_str}.jsonl"

    def _append(self, path: Path, data: Dict[str, Any]) -> None:
        try:
            with self._lock:
                with path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(data, default=str) + "\n")
        except OSError as exc:
            raise StorageException(f"Failed to write to {path}: {exc}") from exc

    # ------------------------------------------------------------------
    # IStorageBackend implementation
    # ------------------------------------------------------------------

    def save_event(self, event: AgentExecutionEvent) -> None:
        self._append(self._dated_path("events"), event.model_dump())

    def save_audit_record(self, record: AuditRecord) -> None:
        self._append(self._dated_path("audits"), record.model_dump())

    def save_metrics(self, metrics: ExecutionMetrics) -> None:
        self._append(self._dated_path("metrics"), metrics.model_dump())

    def save_alert(self, alert: AlertEvent) -> None:
        self._append(self._dated_path("alerts"), alert.model_dump())
