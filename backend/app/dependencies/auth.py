from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from typing import Annotated

from backend.app.dependencies.agents import get_agent_orchestrator
from backend.app.routers.auth import get_auth_service
from backend.app.core.interfaces import IAuthService
from backend.app.schemas.auth import TokenPayload, Role

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

async def require_expert_role(current_user: Annotated[TokenPayload, Depends(get_current_user)]):
    """RBAC validation dependency."""
    if current_user.role not in [Role.EXPERT.value, Role.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user
