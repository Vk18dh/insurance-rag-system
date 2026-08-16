from fastapi import APIRouter, Depends
from typing import Annotated
from backend.app.dependencies.auth import require_expert_role
from backend.app.schemas.auth import TokenPayload

router = APIRouter(prefix="/expert", tags=["expert"])

@router.get("/dashboard")
async def expert_dashboard(current_user: Annotated[TokenPayload, Depends(require_expert_role)]):
    """
    Expert dashboard.
    Only accessible by EXPERT or ADMIN roles.
    """
    return {"message": "Welcome to the expert dashboard", "user": current_user.sub}
