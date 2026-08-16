from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.models.review_task import ReviewTask, ReviewTaskStatus
from backend.app.schemas.review_task import ReviewTaskCreate, ReviewTaskUpdate
from datetime import datetime, timezone

class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ReviewTaskCreate) -> ReviewTask:
        task = ReviewTask(
            conversation_id=data.conversation_id,
            message_id=data.message_id,
            reason=data.reason,
            payload=data.payload
        )
        self.db.add(task)
        self.db.flush()
        return task

    def get_by_id(self, task_id: str) -> Optional[ReviewTask]:
        return self.db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        
    def list_all(self, status: Optional[ReviewTaskStatus] = None) -> List[ReviewTask]:
        query = self.db.query(ReviewTask)
        if status:
            query = query.filter(ReviewTask.status == status)
        return query.order_by(ReviewTask.created_at.desc()).all()

    def update(self, task: ReviewTask, update_data: ReviewTaskUpdate) -> ReviewTask:
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        self.db.flush()
        return task
