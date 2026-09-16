import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from backend.app.db.database import Base

class SecurityAuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    actor_id = Column(String, nullable=True, index=True)
    role = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    target_id = Column(String, nullable=True)
    outcome = Column(String, nullable=False)
    safe_metadata = Column(JSON, nullable=True)
