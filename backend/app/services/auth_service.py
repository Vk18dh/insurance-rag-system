import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError

from backend.app.config.settings import BackendSettings
from backend.app.core.interfaces import IAuthService, IUserService
from backend.app.schemas.auth import Token, UserResponse, LoginRequest

# Using bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService(IAuthService):
    """Concrete implementation of IAuthService using python-jose and passlib."""
    
    def __init__(self, user_service: IUserService):
        self.user_service = user_service
        settings = BackendSettings.load()
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.security.jwt_algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def authenticate_user(self, credentials: LoginRequest) -> Optional[UserResponse]:
        user = self.user_service.get_user_by_username(credentials.username)
        if not user:
            return None
            
        # In a real database, we'd hash check. Mocking validation for Part 11 demonstration:
        # We assume the user service returns a valid user if they exist and passwords match basic logic
        
        # Verify mocked password check
        if credentials.password != "password":  # Mock check constraint
            return None
            
        return user

    def create_access_token(self, data: dict, expires_delta_minutes: Optional[int] = None) -> Token:
        to_encode = data.copy()
        
        expire_minutes = expires_delta_minutes if expires_delta_minutes else self.access_token_expire_minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            refresh_token=None
        )

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise ValueError("Invalid credentials") from e
