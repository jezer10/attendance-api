from fastapi import Depends
from src.services.auth_service import AuthService, security

from fastapi.security import HTTPAuthorizationCredentials


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user"""
    print(credentials)
    return AuthService.get_current_user(credentials)
