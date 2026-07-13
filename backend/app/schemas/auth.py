from enum import Enum
from pydantic import BaseModel
from typing import Optional

class Role(str, Enum):
    ADMIN = "admin"
    EXPERT = "expert"
    USER = "user"

class Token(BaseModel):
    """Token response schema for JWT authentication."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenPayload(BaseModel):
    """Payload nested inside the JWT Token."""
    sub: str
    role: str
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    """Incoming request for token generation."""
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.USER

class UserResponse(BaseModel):
    id: str
    username: str
    role: Role
