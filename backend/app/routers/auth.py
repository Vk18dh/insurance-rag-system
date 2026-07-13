from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from backend.app.schemas.auth import Token, UserResponse, LoginRequest
from backend.app.core.interfaces import IAuthService
from backend.app.services.auth_service import AuthService
from backend.app.services.user_service import MockUserService

router = APIRouter(prefix="/auth", tags=["auth"])

# DI provider for AuthService
def get_auth_service() -> IAuthService:
    user_service = MockUserService()
    return AuthService(user_service=user_service)

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
        data={"sub": user.username, "role": user.role.value}
    )
    return access_token
