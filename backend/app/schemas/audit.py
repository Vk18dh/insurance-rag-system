from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    actor_id: Optional[str] = None
    role: Optional[str] = None
    action: str
    target_id: Optional[str] = None
    outcome: str
    safe_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class AuditLogPaginated(BaseModel):
    items: list[AuditLogResponse]
    total: int
