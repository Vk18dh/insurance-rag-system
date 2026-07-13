"""
phase2.observability.models.audit_record
=========================================
Audit trail entry.

Security rules (Part 0 + Part 9):
  - Raw query text is NEVER stored.
  - Query is stored as a SHA-256 hex digest (salted via env var).
  - No API keys, prompts, or PII are written to audit records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    """
    Complete audit entry for one pipeline execution.

    Fields
    ------
    execution_id        : Distributed trace ID (UUID v4).
    query_hash          : SHA-256(salt + query_text) — never the raw query.
    request_timestamp   : UTC time the pipeline was initiated.
    completion_timestamp: UTC time the pipeline returned a response (or failed).
    agent_sequence      : Ordered list of agent names that executed.
    retrieved_doc_ids   : IDs of documents retrieved (no content stored).
    warning_count       : Number of warnings emitted.
    exception_types     : List of exception class names (no messages — prevents PII leakage).
    citation_count      : Number of citations included in the final response.
    overall_status      : "success" | "failure" | "partial".
    environment         : Runtime environment label (development / production …).
    """

    execution_id: str = Field(..., description="Distributed trace ID.")
    query_hash: str = Field(
        ...,
        description="SHA-256 hex digest of (salt + raw_query). Never contains the raw query.",
    )
    request_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completion_timestamp: Optional[datetime] = Field(default=None)
    agent_sequence: List[str] = Field(default_factory=list)
    retrieved_doc_ids: List[str] = Field(default_factory=list)
    warning_count: int = Field(default=0, ge=0)
    exception_types: List[str] = Field(
        default_factory=list,
        description="Exception class names only — no messages.",
    )
    citation_count: int = Field(default=0, ge=0)
    overall_status: str = Field(default="success")
    environment: str = Field(default="development")
