import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from postgrest.exceptions import APIError
from supabase import Client, create_client
from supabase_auth.errors import AuthApiError

from core.config import settings

security = HTTPBearer()
logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        print(settings.supabase_service_key)
        _supabase_client = create_client(
            settings.supabase_url, settings.supabase_service_key
        )
    return _supabase_client


class AuthService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token against Supabase"""
        client = get_supabase_client()
        try:
            user_response = client.auth.get_user(token)
        except AuthApiError as exc:
            logger.warning("Supabase rejected token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            ) from exc
        except APIError as exc:
            logger.error("Supabase API error while validating token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication provider unavailable",
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error validating token")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to validate authentication token",
            ) from exc

        if user_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "role": user_response.user.role,
            "audience": user_response.user.aud,
        }

    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials) -> dict:
        """Get current user from token"""
        token = credentials.credentials
        return AuthService.verify_token(token)
