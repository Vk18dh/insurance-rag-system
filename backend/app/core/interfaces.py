from abc import ABC, abstractmethod
from typing import Optional
from backend.app.schemas.auth import Token, UserResponse, UserCreate, LoginRequest

class IAuthService(ABC):
    """Protocol for generating and validating API tokens."""
    
    @abstractmethod
    def authenticate_user(self, credentials: LoginRequest) -> Optional[UserResponse]:
        """Validates credentials and returns user payload if authentic."""
        pass
        
    @abstractmethod
    def create_access_token(self, data: dict, expires_delta_minutes: Optional[int] = None) -> Token:
        """Returns signed JWT mapping."""
        pass
        
    @abstractmethod
    def decode_access_token(self, token: str) -> dict:
        """Decodes JWT payload."""
        pass

class IUserService(ABC):
    """Protocol for user data retrieval (Mocked for Part 11)."""
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        pass
        
    @abstractmethod
    def create_user(self, request: UserCreate) -> UserResponse:
        pass
