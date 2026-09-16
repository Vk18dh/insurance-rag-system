from sqlalchemy.orm import Session
from backend.app.models.audit import SecurityAuditLog
from backend.app.schemas.audit import AuditLogResponse
from typing import Optional, List

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_log: SecurityAuditLog) -> SecurityAuditLog:
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def list(self, skip: int = 0, limit: int = 50, action: Optional[str] = None, actor_id: Optional[str] = None) -> tuple[List[SecurityAuditLog], int]:
        query = self.db.query(SecurityAuditLog)
        
        if action:
            query = query.filter(SecurityAuditLog.action == action)
        if actor_id:
            query = query.filter(SecurityAuditLog.actor_id == actor_id)
            
        total = query.count()
        items = query.order_by(SecurityAuditLog.timestamp.desc()).offset(skip).limit(limit).all()
        
        return items, total
