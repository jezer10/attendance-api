from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

import logging
from datetime import datetime

from models import AttendanceRequest, AttendanceResponse, HealthResponse
from services.attendance_service import AttendanceService
from services.auth_service import AuthService, security
from exceptions import AuthenticationError, NetworkError, AttendanceAPIException

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user"""
    return AuthService.get_current_user(credentials)


@router.post("/attendance", response_model=AttendanceResponse)
async def mark_attendance(
    request_body: AttendanceRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Mark attendance (entry or exit)"""
    try:
        async with AttendanceService() as service:
            result = await service.process_attendance(request_body)

        if not result.success:
            logger.warning(
                f"Attendance failed for user {request_body.credentials.user_id}: {result.message}"
            )
            raise AttendanceAPIException(result.message)

        logger.info(
            f"Attendance successful for user {request_body.credentials.user_id}"
        )
        return result

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    except NetworkError as e:
        logger.error(f"Network error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External service temporarily unavailable",
        )

    except AttendanceAPIException as e:
        logger.error(f"Attendance API error: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "type": None,
                "title": "Attendance marking failed",
                "status": status.HTTP_400_BAD_REQUEST,
                "detail": str(e),
                "instance": str(request.url),
            },
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", service="attendance-api", timestamp=datetime.now()
    )


@router.post("/auth/token")
async def create_token(user_data: dict):
    """Create authentication token (for testing purposes)"""
    token = AuthService.create_access_token(data=user_data)
    return {"access_token": token, "token_type": "bearer"}
