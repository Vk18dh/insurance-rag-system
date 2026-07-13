"""
phase2.observability.tests.test_observability
=============================================
Unit and integration tests for the Observability Layer.

Tests comply with Part 0:
  - No live LLM / ChromaDB calls.
  - All dependencies are mocked or constructed in-process.
  - Each test is isolated and idempotent.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
from phase2.observability.models.observability_event import (
    AgentExecutionEvent, EventType,
)
from phase2.observability.models.audit_record import AuditRecord
from phase2.observability.models.execution_metrics import AgentMetrics, ExecutionMetrics
from phase2.observability.models.trace_context import TraceContext
from phase2.observability.models.health_snapshot import HealthSnapshot
from phase2.observability.models.alert_event import AlertEvent, AlertSeverity

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
from phase2.observability.metrics.metrics_service import MetricsService
from phase2.observability.tracing.tracing_service import TracingService
from phase2.observability.audit.audit_service import AuditService
from phase2.observability.health.health_monitor import HealthMonitor
from phase2.observability.storage.json_storage import JsonStorageBackend
from phase2.observability.storage.sqlite_storage import SqliteStorageBackend
from phase2.observability.facade import ObservabilityFacade, NullObservabilityFacade, ObservabilityFactory
from phase2.observability.logging.logging_service import LoggingService
from phase2.observability.exceptions import MetricsException, AuditException


# ===========================================================================
# Model Tests
# ===========================================================================

class TestModels:
    def test_trace_context_child_span_inherits_execution_id(self):
        root = TraceContext()
        child = root.child_span()
        assert child.execution_id == root.execution_id
        assert child.parent_span_id == root.span_id
        assert child.span_id != root.span_id

    def test_agent_execution_event_frozen(self):
        evt = AgentExecutionEvent(
            event_type=EventType.AGENT_STARTED,
            execution_id="exec-1",
            agent_name="TestAgent",
        )
        with pytest.raises(Exception):
            evt.agent_name = "Modified"  # type: ignore

    def test_audit_record_defaults(self):
        rec = AuditRecord(execution_id="x", query_hash="abc123")
        assert rec.warning_count == 0
        assert rec.overall_status == "success"

    def test_health_snapshot_is_healthy_default(self):
        snap = HealthSnapshot()
        assert snap.is_healthy is True
        assert snap.unhealthy_reasons == []


# ===========================================================================
# MetricsService Tests
# ===========================================================================

class TestMetricsService:
    def setup_method(self):
        self.svc = MetricsService()

    def test_basic_lifecycle(self):
        eid = "exec-1"
        t0 = time.time() * 1000
        self.svc.record_agent_start(eid, "AgentA", t0)
        time.sleep(0.01)
        t1 = time.time() * 1000
        self.svc.record_agent_end(eid, "AgentA", t1, succeeded=True)
        metrics = self.svc.compile_execution_metrics(eid)
        assert metrics.execution_id == eid
        assert len(metrics.agent_metrics) == 1
        assert metrics.agent_metrics[0].succeeded is True
        assert metrics.agent_metrics[0].duration_ms > 0

    def test_multiple_agents(self):
        eid = "exec-2"
        t = time.time() * 1000
        for name in ["A", "B", "C"]:
            self.svc.record_agent_start(eid, name, t)
            self.svc.record_agent_end(eid, name, t + 50, succeeded=True)
        metrics = self.svc.compile_execution_metrics(eid)
        assert len(metrics.agent_metrics) == 3

    def test_missing_start_raises(self):
        svc = MetricsService()
        with pytest.raises(MetricsException):
            svc.record_agent_end("no-start", "AgentX", 9999.0, succeeded=True)

    def test_thread_safety(self):
        """Concurrent goroutine-style test using threads."""
        svc = MetricsService()
        errors = []

        def run(idx: int):
            try:
                eid = f"exec-{idx}"
                t = time.time() * 1000
                svc.record_agent_start(eid, "Worker", t)
                svc.record_agent_end(eid, "Worker", t + 10, succeeded=True)
                svc.compile_execution_metrics(eid)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run, args=(i,)) for i in range(20)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        assert errors == []


# ===========================================================================
# TracingService Tests
# ===========================================================================

class TestTracingService:
    def test_start_trace_returns_unique_ids(self):
        svc = TracingService()
        t1 = svc.start_trace()
        t2 = svc.start_trace()
        assert t1.execution_id != t2.execution_id

    def test_child_span_inherits_execution_id(self):
        svc = TracingService()
        root = svc.start_trace()
        child = svc.start_span(root)
        assert child.execution_id == root.execution_id
        assert child.parent_span_id == root.span_id


# ===========================================================================
# AuditService Tests
# ===========================================================================

class TestAuditService:
    def test_query_is_hashed_not_stored(self):
        svc = AuditService(salt_env_var="OBSERVABILITY_SALT", environment="testing")
        raw = "What is my coverage?"
        rec = svc.create_record("exec-1", raw, "testing")
        assert raw not in rec.query_hash
        assert len(rec.query_hash) == 64  # SHA-256 hex = 64 chars

    def test_finalise_populates_fields(self):
        svc = AuditService(salt_env_var="OBSERVABILITY_SALT", environment="testing")
        svc.create_record("exec-2", "query", "testing")
        final = svc.finalise_record(
            execution_id="exec-2",
            agent_sequence=["A", "B"],
            warning_count=1,
            citation_count=3,
            overall_status="success",
        )
        assert final.agent_sequence == ["A", "B"]
        assert final.warning_count == 1
        assert final.citation_count == 3

    def test_missing_record_raises(self):
        svc = AuditService(salt_env_var="OBSERVABILITY_SALT", environment="testing")
        with pytest.raises(AuditException):
            svc.finalise_record("no-such-id", [], 0, 0, "success")


# ===========================================================================
# Storage Backend Tests
# ===========================================================================

class TestJsonStorage:
    def test_save_audit_creates_file(self, tmp_path):
        storage = JsonStorageBackend(audit_dir=str(tmp_path))
        rec = AuditRecord(execution_id="e1", query_hash="abc")
        storage.save_audit_record(rec)
        jsonl_files = list(tmp_path.glob("audits_*.jsonl"))
        assert len(jsonl_files) == 1
        content = jsonl_files[0].read_text()
        assert "e1" in content
        assert "abc" in content

    def test_save_event_creates_file(self, tmp_path):
        storage = JsonStorageBackend(audit_dir=str(tmp_path))
        evt = AgentExecutionEvent(
            event_type=EventType.AGENT_COMPLETED,
            execution_id="e2",
            agent_name="TestAgent",
        )
        storage.save_event(evt)
        files = list(tmp_path.glob("events_*.jsonl"))
        assert len(files) == 1


class TestSqliteStorage:
    def test_save_audit_and_retrieve(self, tmp_path):
        db = str(tmp_path / "obs.db")
        storage = SqliteStorageBackend(db_path=db)
        rec = AuditRecord(execution_id="s1", query_hash="xyz")
        storage.save_audit_record(rec)
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT execution_id FROM obs_audits").fetchall()
        conn.close()
        assert any("s1" in r[0] for r in rows)

    def test_thread_safe_writes(self, tmp_path):
        db = str(tmp_path / "obs_thread.db")
        storage = SqliteStorageBackend(db_path=db)
        errors = []

        def write(idx: int):
            try:
                rec = AuditRecord(execution_id=f"exec-{idx}", query_hash=f"hash-{idx}")
                storage.save_audit_record(rec)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


# ===========================================================================
# HealthMonitor Tests
# ===========================================================================

class TestHealthMonitor:
    def test_healthy_by_default(self):
        monitor = HealthMonitor(failure_rate_threshold=0.3, avg_latency_ms_threshold=5000.0)
        snap = monitor.get_health_snapshot()
        assert snap.is_healthy is True

    def test_alert_on_high_failure_rate(self):
        monitor = HealthMonitor(failure_rate_threshold=0.3, avg_latency_ms_threshold=5000.0)
        # Inject 4 failures out of 5 = 80% failure rate
        for i in range(5):
            monitor.record_execution_outcome(f"exec-{i}", succeeded=(i == 0), duration_ms=100.0, had_timeout=False, retry_count=0)
        alerts = monitor.get_pending_alerts()
        assert any(a.metric_name == "failure_rate" for a in alerts)

    def test_no_alert_below_threshold(self):
        monitor = HealthMonitor(failure_rate_threshold=0.5, avg_latency_ms_threshold=5000.0)
        for i in range(10):
            monitor.record_execution_outcome(f"exec-{i}", succeeded=True, duration_ms=10.0, had_timeout=False, retry_count=0)
        alerts = monitor.get_pending_alerts()
        assert alerts == []


# ===========================================================================
# NullObservabilityFacade Tests
# ===========================================================================

class TestNullFacade:
    def test_no_op_does_not_raise(self):
        facade = NullObservabilityFacade()
        trace = facade.on_pipeline_start("exec-null", "any query")
        span = facade.on_agent_start(trace, "SomeAgent")
        facade.on_agent_end(span, "SomeAgent", 10.0, True)
        facade.on_pipeline_end(trace, "success")


# ===========================================================================
# Integration Test — Full Pipeline Observability
# ===========================================================================

class TestIntegration:
    def test_full_pipeline_trace(self, tmp_path):
        """Simulate a complete 3-agent pipeline and verify all artifacts are created."""
        from phase2.observability.logging.logging_service import LoggingService
        from phase2.observability.metrics.metrics_service import MetricsService
        from phase2.observability.audit.audit_service import AuditService
        from phase2.observability.tracing.tracing_service import TracingService
        from phase2.observability.health.health_monitor import HealthMonitor
        from phase2.observability.storage.json_storage import JsonStorageBackend

        logging_svc = LoggingService("DEBUG", str(tmp_path / "logs"), True, False, "text")
        metrics_svc = MetricsService()
        audit_svc = AuditService("OBSERVABILITY_SALT", "testing")
        tracing_svc = TracingService()
        health = HealthMonitor(0.3, 5000.0)
        storage = JsonStorageBackend(audit_dir=str(tmp_path / "audits"))

        facade = ObservabilityFacade(
            logging_svc=logging_svc,
            metrics_svc=metrics_svc,
            audit_svc=audit_svc,
            tracing_svc=tracing_svc,
            storage=storage,
            health_monitor=health,
            environment="testing",
        )

        exec_id = "integration-1"
        agents = ["QueryAgent", "RetrievalAgent", "ResponseBuilder"]

        trace = facade.on_pipeline_start(exec_id, "What is my deductible?")

        for agent in agents:
            span = facade.on_agent_start(trace, agent)
            time.sleep(0.005)
            facade.on_agent_end(span, agent, 5.0, succeeded=True)

        facade.on_pipeline_end(trace, "success", warning_count=0, citation_count=2)

        audit_files = list((tmp_path / "audits").glob("audits_*.jsonl"))
        assert len(audit_files) == 1
        content = audit_files[0].read_text()
        assert exec_id in content
        assert "What" not in content  # raw query must not appear
