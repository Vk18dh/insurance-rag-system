from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from backend.app.schemas.auth import Token, UserResponse, LoginRequest, UserCreate
from backend.app.core.interfaces import IAuthService
from backend.app.dependencies.auth import get_auth_service
from backend.app.dependencies.db import get_db
from sqlalchemy.orm import Session
from backend.app.services.user_service import UserService
from backend.app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    repo = UserRepository(db)
    return UserService(user_repository=repo)

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    auth_service: IAuthService = Depends(get_auth_service)
):
    """OAuth2 compatible token login, required for Swagger UI integration."""
    creds = LoginRequest(username=form_data.username, password=form_data.password)
    user = auth_service.authenticate_user(creds)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )
    return access_token

@router.post("/register", response_model=UserResponse)
async def register(
    request: UserCreate,
    user_service: UserService = Depends(get_user_service),
    auth_service: IAuthService = Depends(get_auth_service)
):
    """Register a new user."""
    # Check if exists
    if user_service.get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # We should have hashed the password before saving
    hashed_password = auth_service.get_password_hash(request.password)
    user = user_service.create_user_with_hash(request, hashed_password)
    user_service.user_repository.db.commit()
    return user

