from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List
from datetime import datetime
from backend.app.models.review_task import ReviewTaskStatus

class ReviewTaskBase(BaseModel):
    conversation_id: str
    message_id: Optional[str] = None
    reason: str
    payload: Any

class ReviewTaskCreate(ReviewTaskBase):
    pass

class ReviewTaskUpdate(BaseModel):
    status: Optional[ReviewTaskStatus] = None
    assigned_expert_id: Optional[str] = None
    expert_decision: Optional[str] = None
    corrected_answer: Optional[str] = None
    expert_comment: Optional[str] = None
    completed_at: Optional[datetime] = None

class ReviewTaskAction(BaseModel):
    decision: str # "APPROVE", "CORRECT"
    corrected_answer: Optional[str] = None
    comment: Optional[str] = None

class ReviewTaskResponse(ReviewTaskBase):
    id: str
    status: ReviewTaskStatus
    created_at: datetime
    assigned_expert_id: Optional[str]
    completed_at: Optional[datetime]
    expert_decision: Optional[str]
    corrected_answer: Optional[str]
    expert_comment: Optional[str]

    model_config = ConfigDict(from_attributes=True)
