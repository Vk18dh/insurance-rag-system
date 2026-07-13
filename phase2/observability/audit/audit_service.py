"""
phase2.observability.audit.audit_service
==========================================
Concrete IAuditService implementation.

Security contract:
  - Raw query text is NEVER persisted.
  - Queries are stored as SHA-256(HMAC with salt from env var).
  - If the env var is missing, a per-process random salt is used (logged as WARNING).
  - No API keys, prompts, or PII are written.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from phase2.observability.interfaces.observability_interface import IAuditService
from phase2.observability.models.audit_record import AuditRecord
from phase2.observability.exceptions import AuditException

logger = logging.getLogger(__name__)

# Per-process fallback salt (used only if OBSERVABILITY_SALT env var is absent)
_FALLBACK_SALT = os.urandom(32).hex()


class AuditService(IAuditService):
    """
    Thread-safe, in-memory audit record store.

    Records are initialised at pipeline start and finalised at pipeline end
    before being flushed to the storage backend by ObservabilityFacade.
    """

    def __init__(self, salt_env_var: str, environment: str) -> None:
        """
        Parameters
        ----------
        salt_env_var : Name of the environment variable holding the HMAC salt.
        environment  : Runtime environment label (e.g. "development").
        """
        self._environment = environment
        raw_salt = os.environ.get(salt_env_var)
        if raw_salt:
            self._salt = raw_salt.encode()
        else:
            logger.warning(
                "Audit salt env var '%s' not set. Using a per-process random salt. "
                "Query hashes will not be reproducible across restarts.",
                salt_env_var,
            )
            self._salt = _FALLBACK_SALT.encode()

        self._lock = threading.Lock()
        self._records: Dict[str, AuditRecord] = {}

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _hash_query(self, raw_query: str) -> str:
        """Return HMAC-SHA256 hex digest of the raw query."""
        return hmac.new(self._salt, raw_query.encode("utf-8"), hashlib.sha256).hexdigest()

    # ------------------------------------------------------------------
    # IAuditService implementation
    # ------------------------------------------------------------------

    def create_record(
        self, execution_id: str, raw_query: str, environment: str
    ) -> AuditRecord:
        record = AuditRecord(
            execution_id=execution_id,
            query_hash=self._hash_query(raw_query),
            environment=environment,
        )
        with self._lock:
            self._records[execution_id] = record
        return record

    def finalise_record(
        self,
        execution_id: str,
        agent_sequence: List[str],
        warning_count: int,
        citation_count: int,
        overall_status: str,
        retrieved_doc_ids: Optional[List[str]] = None,
        exception_types: Optional[List[str]] = None,
    ) -> AuditRecord:
        with self._lock:
            record = self._records.get(execution_id)
            if record is None:
                raise AuditException(
                    f"Audit record not found for execution_id={execution_id}"
                )
            updated = record.model_copy(
                update={
                    "completion_timestamp": datetime.now(timezone.utc),
                    "agent_sequence": agent_sequence,
                    "warning_count": warning_count,
                    "citation_count": citation_count,
                    "overall_status": overall_status,
                    "retrieved_doc_ids": retrieved_doc_ids or [],
                    "exception_types": exception_types or [],
                }
            )
            self._records[execution_id] = updated
        return updated

    def get_record(self, execution_id: str) -> Optional[AuditRecord]:
        with self._lock:
            return self._records.get(execution_id)

    def pop_record(self, execution_id: str) -> Optional[AuditRecord]:
        """Remove and return a completed record (called by facade before flush)."""
        with self._lock:
            return self._records.pop(execution_id, None)
