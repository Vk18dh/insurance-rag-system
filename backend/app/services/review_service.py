from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.models.review_task import ReviewTaskStatus
from backend.app.schemas.review_task import ReviewTaskCreate, ReviewTaskUpdate, ReviewTaskAction, ReviewTaskResponse
from backend.app.repositories.review_repository import ReviewRepository
from fastapi import HTTPException

class ReviewService:
    def __init__(self, review_repository: ReviewRepository):
        self.repo = review_repository

    def create_task(self, data: ReviewTaskCreate) -> ReviewTaskResponse:
        task = self.repo.create(data)
        return ReviewTaskResponse.model_validate(task)

    def get_task(self, task_id: str) -> ReviewTaskResponse:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Review task not found")
        return ReviewTaskResponse.model_validate(task)

    def list_tasks(self, status: Optional[ReviewTaskStatus] = None) -> List[ReviewTaskResponse]:
        tasks = self.repo.list_all(status)
        return [ReviewTaskResponse.model_validate(t) for t in tasks]

    def process_action(self, task_id: str, expert_id: str, action: ReviewTaskAction) -> ReviewTaskResponse:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Review task not found")
            
        if task.status not in [ReviewTaskStatus.PENDING, ReviewTaskStatus.IN_REVIEW]:
            raise HTTPException(status_code=400, detail=f"Cannot process task in status {task.status}")

        if action.decision == "APPROVE":
            new_status = ReviewTaskStatus.APPROVED
        elif action.decision == "CORRECT":
            new_status = ReviewTaskStatus.CORRECTED
        else:
            raise HTTPException(status_code=400, detail=f"Invalid decision {action.decision}")

        update_data = ReviewTaskUpdate(
            status=new_status,
            assigned_expert_id=expert_id,
            expert_decision=action.decision,
            corrected_answer=action.corrected_answer,
            expert_comment=action.comment,
            completed_at=datetime.now(timezone.utc)
        )
        
        updated_task = self.repo.update(task, update_data)
        return ReviewTaskResponse.model_validate(updated_task)
