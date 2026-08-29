from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List, Optional
from backend.app.dependencies.auth import require_expert_role
from backend.app.schemas.auth import TokenPayload
from backend.app.schemas.review_task import ReviewTaskResponse, ReviewTaskAction
from backend.app.models.review_task import ReviewTaskStatus
from backend.app.dependencies.review import get_review_service
from backend.app.services.review_service import ReviewService

router = APIRouter(prefix="/expert", tags=["expert"])

@router.get("/dashboard")
async def expert_dashboard(current_user: Annotated[TokenPayload, Depends(require_expert_role)]):
    """
    Expert dashboard.
    Only accessible by EXPERT or ADMIN roles.
    """
    return {"message": "Welcome to the expert dashboard", "user": current_user.sub}

@router.get("/reviews", response_model=List[ReviewTaskResponse])
async def list_reviews(
    current_user: Annotated[TokenPayload, Depends(require_expert_role)],
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    status: Optional[ReviewTaskStatus] = None
):
    """List all review tasks, optionally filtered by status."""
    return review_service.list_tasks(status=status)

@router.get("/reviews/{task_id}", response_model=ReviewTaskResponse)
async def get_review(
    task_id: str,
    current_user: Annotated[TokenPayload, Depends(require_expert_role)],
    review_service: Annotated[ReviewService, Depends(get_review_service)]
):
    """Get a specific review task by ID."""
    return review_service.get_task(task_id)

@router.post("/reviews/{task_id}/action", response_model=ReviewTaskResponse)
async def process_review_action(
    task_id: str,
    action: ReviewTaskAction,
    current_user: Annotated[TokenPayload, Depends(require_expert_role)],
    review_service: Annotated[ReviewService, Depends(get_review_service)]
):
    """Process an expert action (APPROVE or CORRECT) on a review task."""
    # current_user.sub is the username, we can use it as expert_id, or we'd need user.id
    # For now, sub is used as expert_id
    result = review_service.process_action(task_id, expert_id=current_user.sub, action=action)
    review_service.repo.db.commit()
    return result
