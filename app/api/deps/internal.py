from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
) -> None:
    if not settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API key is not configured",
        )
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )
