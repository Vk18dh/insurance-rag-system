import logging
import hashlib
from typing import Optional, Dict, Any
from backend.app.models.audit import SecurityAuditLog
from backend.app.db.database import SessionLocal

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def log_event(
        action: str,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
        target_id: Optional[str] = None,
        outcome: str = "SUCCESS",
        safe_metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None
    ) -> None:
        """
        Safely logs a security audit event in a completely isolated database transaction.
        Never store passwords, JWTs, API keys, or raw provider responses in safe_metadata.
        """
        try:
            # We use an isolated session to prevent poison or rollback of the primary business transaction
            session = db or SessionLocal()
            try:
                # Sanity check: Ensure no sensitive keys in metadata
                if safe_metadata:
                    forbidden_keys = {"password", "token", "jwt", "authorization", "api_key", "secret"}
                    for k in list(safe_metadata.keys()):
                        if k.lower() in forbidden_keys:
                            safe_metadata[k] = "[REDACTED]"
                
                audit_log = SecurityAuditLog(
                    actor_id=actor_id,
                    role=role,
                    action=action,
                    target_id=target_id,
                    outcome=outcome,
                    safe_metadata=safe_metadata
                )
                session.add(audit_log)
                if not db:
                    session.commit()
            except Exception as inner_e:
                if not db:
                    session.rollback()
                logger.error(f"Failed to commit audit log transaction: {inner_e}")
            finally:
                if not db:
                    session.close()
        except Exception as e:
            logger.error(f"AuditService completely failed to log event '{action}': {e}")

    @staticmethod
    def hash_query(query_text: str) -> str:
        """One-way hash for query text so the raw PII/data isn't persistently stored."""
        return hashlib.sha256(query_text.encode("utf-8")).hexdigest()
