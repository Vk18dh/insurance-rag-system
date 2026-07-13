from typing import Optional
from backend.app.core.interfaces import IUserService
from backend.app.schemas.auth import UserResponse, UserCreate, Role


class MockUserService(IUserService):
    """
    Mock user database service. Provides static authentication profiles.
    Used exclusively to demonstrate JWT and RBAC functionality through FastAPI.
    """
    
    def __init__(self):
        self.mock_db = {
            "admin_user": UserResponse(id="u1", username="admin_user", role=Role.ADMIN),
            "expert_user": UserResponse(id="u2", username="expert_user", role=Role.EXPERT),
            "standard_user": UserResponse(id="u3", username="standard_user", role=Role.USER)
        }

    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        return self.mock_db.get(username)

    def create_user(self, request: UserCreate) -> UserResponse:
        # Dynamic mock insert
        new_id = f"u{len(self.mock_db) + 1}"
        new_user = UserResponse(id=new_id, username=request.username, role=request.role)
        self.mock_db[request.username] = new_user
        return new_user
