from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.services.auth import decode_access_token
from app.schemas.user import TokenData
from app.database import get_database

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Get current active user (verified)."""
    # Could add verification check here if needed
    return current_user


async def get_admin_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class OptionalAuth:
    """Optional authentication dependency."""
    
    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        )
    ) -> Optional[TokenData]:
        if credentials is None:
            return None
        
        token_data = decode_access_token(credentials.credentials)
        return token_data


optional_auth = OptionalAuth()
