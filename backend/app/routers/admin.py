from fastapi import APIRouter, Depends
from typing import Annotated
from backend.app.dependencies.auth import require_admin_role
from backend.app.schemas.auth import TokenPayload

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
async def admin_dashboard(current_user: Annotated[TokenPayload, Depends(require_admin_role)]):
    """
    Admin dashboard.
    Only accessible by ADMIN role.
    """
    return {"message": "Welcome to the admin dashboard", "user": current_user.sub}
