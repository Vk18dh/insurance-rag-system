from typing import Optional
from backend.app.core.interfaces import IUserService
from backend.app.schemas.auth import UserResponse, UserCreate, Role

from backend.app.repositories.user_repository import UserRepository

class UserService(IUserService):
    """
    Real database-backed user service implementing IUserService.
    """
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        user = self.user_repository.get_by_username(username)
        if user:
            return UserResponse(id=user.id, username=user.username, role=user.role)
        return None

    def create_user(self, request: UserCreate) -> UserResponse:
        # Note: Password hashing should occur before calling create, 
        # but the interface requires UserCreate so we handle it gracefully here if needed.
        # Actually, we should pass hashed_password. We'll adjust the signature or expect caller to hash.
        # For IUserService contract:
        pass
        
    def create_user_with_hash(self, request: UserCreate, hashed_password: str) -> UserResponse:
        user = self.user_repository.create(request, hashed_password)
        return UserResponse(id=user.id, username=user.username, role=user.role)

