import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON
from backend.app.db.database import Base

class ReviewTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    CORRECTED = "CORRECTED"
    CANCELLED = "CANCELLED"

class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True) # Optional message link
    status = Column(Enum(ReviewTaskStatus), default=ReviewTaskStatus.PENDING, nullable=False)
    reason = Column(String, nullable=False)
    
    # Store a snapshot of the context for the expert
    payload = Column(JSON, nullable=False) # Contains query, answer, evidence, citations, risk, reasoning
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    assigned_expert_id = Column(String, ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Review details
    expert_decision = Column(String, nullable=True)
    corrected_answer = Column(String, nullable=True)
    expert_comment = Column(String, nullable=True)
