from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from typing import Annotated

from backend.app.dependencies.agents import get_agent_orchestrator
from backend.app.core.interfaces import IAuthService
from backend.app.schemas.auth import TokenPayload, Role
from sqlalchemy.orm import Session
from backend.app.dependencies.db import get_db
from backend.app.repositories.user_repository import UserRepository
from backend.app.services.auth_service import AuthService

def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> IAuthService:
    repo = UserRepository(db)
    return AuthService(user_repository=repo)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: IAuthService = Depends(get_auth_service)
) -> TokenPayload:
    """Dependency injecting the current authenticated user context mapping."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth_service.decode_access_token(token)
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
            
        token_data = TokenPayload(sub=username, role=role)
        return token_data
        
    except ValueError: # Mapping JWTError raised in AuthService as ValueError
        raise credentials_exception

async def require_user_role(current_user: Annotated[TokenPayload, Depends(get_current_user)]):
    """RBAC validation dependency for standard user."""
    # ANY authenticated user can access user endpoints
    return current_user

async def require_expert_role(current_user: Annotated[TokenPayload, Depends(get_current_user)]):
    """RBAC validation dependency for expert."""
    if current_user.role not in [Role.EXPERT.value, Role.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

async def require_admin_role(current_user: Annotated[TokenPayload, Depends(get_current_user)]):
    """RBAC validation dependency for admin."""
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user
