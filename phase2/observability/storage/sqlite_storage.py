"""
phase2.observability.storage.sqlite_storage
============================================
SQLite storage backend.

Uses Python's built-in sqlite3 — no additional dependencies.
Database path is configured via ObservabilitySettings — never hardcoded.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from phase2.observability.interfaces.observability_interface import IStorageBackend
from phase2.observability.models.observability_event import AgentExecutionEvent
from phase2.observability.models.audit_record import AuditRecord
from phase2.observability.models.execution_metrics import ExecutionMetrics
from phase2.observability.models.alert_event import AlertEvent
from phase2.observability.exceptions import StorageException

_DDL = """
CREATE TABLE IF NOT EXISTS obs_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    agent_name   TEXT,
    timestamp    TEXT NOT NULL,
    payload      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS obs_audits (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    query_hash   TEXT NOT NULL,
    status       TEXT NOT NULL,
    payload      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS obs_metrics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    total_ms     REAL,
    payload      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS obs_alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id     TEXT NOT NULL UNIQUE,
    severity     TEXT NOT NULL,
    metric_name  TEXT NOT NULL,
    payload      TEXT NOT NULL
);
"""


class SqliteStorageBackend(IStorageBackend):
    """Thread-safe SQLite-backed observability store."""

    def __init__(self, db_path: str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = str(path)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_DDL)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, check_same_thread=False)

    # ------------------------------------------------------------------
    # IStorageBackend implementation
    # ------------------------------------------------------------------

    def save_event(self, event: AgentExecutionEvent) -> None:
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    "INSERT INTO obs_events (execution_id, event_type, agent_name, timestamp, payload) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        event.execution_id,
                        event.event_type.value,
                        event.agent_name,
                        event.timestamp_utc.isoformat(),
                        json.dumps(event.model_dump(), default=str),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageException(f"SQLite save_event failed: {exc}") from exc

    def save_audit_record(self, record: AuditRecord) -> None:
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO obs_audits (execution_id, query_hash, status, payload) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        record.execution_id,
                        record.query_hash,
                        record.overall_status,
                        json.dumps(record.model_dump(), default=str),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageException(f"SQLite save_audit_record failed: {exc}") from exc

    def save_metrics(self, metrics: ExecutionMetrics) -> None:
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO obs_metrics (execution_id, total_ms, payload) "
                    "VALUES (?, ?, ?)",
                    (
                        metrics.execution_id,
                        metrics.total_duration_ms,
                        json.dumps(metrics.model_dump(), default=str),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageException(f"SQLite save_metrics failed: {exc}") from exc

    def save_alert(self, alert: AlertEvent) -> None:
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO obs_alerts (alert_id, severity, metric_name, payload) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        alert.alert_id,
                        alert.severity.value,
                        alert.metric_name,
                        json.dumps(alert.model_dump(), default=str),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageException(f"SQLite save_alert failed: {exc}") from exc
