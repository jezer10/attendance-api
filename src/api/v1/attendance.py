from models import AttendanceRequest, AttendanceResponse, HealthResponse
from fastapi import  HTTPException, Depends, status
from src.services.attendance_service import AttendanceService
from fastapi import APIRouter
from exceptions import ValidationError
from src.api.deps.auth import get_current_user

import logging
logger = logging.getLogger(__name__)
attendance_service = AttendanceService()
router = APIRouter()

@router.post("/attendance", response_model=AttendanceResponse)
async def mark_attendance(
    request_body: AttendanceRequest, current_user: dict = Depends(get_current_user)
) -> AttendanceResponse:
    """Mark attendance (entry or exit)"""
    try:
        result = attendance_service.process_attendance(request_body)
        logger.info(
            "Attendance successful for user %s", request_body.credentials.user_id
        )
        return result
    except ValidationError as exc:
        logger.warning("Attendance validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
