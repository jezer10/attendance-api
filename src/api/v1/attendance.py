from src.models import (
    AttendanceRequest,
    AttendanceResponse,
    AttendanceNotifyRequest,
    AttendanceNotifyResponse,
)
from fastapi import HTTPException, Depends, status
from src.services.attendance_service import AttendanceService
from fastapi import APIRouter
from src.exceptions import (
    NotFoundError,
    PersistenceError,
    ValidationError,
    NotificationError,
)
from src.api.deps.auth import get_current_user

import logging

logger = logging.getLogger(__name__)
attendance_service = AttendanceService()
router = APIRouter()


@router.put("", response_model=AttendanceResponse, response_model_by_alias=True)
async def mark_attendance(
    request_body: AttendanceRequest, current_user: dict = Depends(get_current_user)
) -> AttendanceResponse:
    """Mark attendance (entry or exit)"""
    try:
        result = attendance_service.process_attendance(
            request_body, current_user=current_user
        )
        logger.info(
            "Attendance schedule processed for user %s",
            current_user.get("id", "unknown"),
        )
        return result
    except ValidationError as exc:
        logger.warning("Attendance validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist attendance schedule: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get("", response_model=AttendanceRequest, response_model_by_alias=True)
async def get_attendance(
    current_user: dict = Depends(get_current_user),
) -> AttendanceRequest:
    """Retrieve the stored attendance schedule for the authenticated user."""
    try:
        result = attendance_service.get_attendance_schedule(current_user=current_user)
        logger.info(
            "Attendance schedule fetched for user %s", current_user.get("id", "unknown")
        )
        return result
    except NotFoundError as exc:
        logger.info("Attendance schedule not found for user %s", current_user.get("id"))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to fetch attendance schedule: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/notify",
    response_model=AttendanceNotifyResponse,
    response_model_by_alias=True,
)
async def notify_attendance(
    request_body: AttendanceNotifyRequest,
    current_user: dict = Depends(get_current_user),
) -> AttendanceNotifyResponse:
    """Send WhatsApp notification for an attendance event."""
    try:
        result = await attendance_service.notify_attendance_event(
            event_id=request_body.event_id, current_user=current_user
        )
        return AttendanceNotifyResponse(
            success=result["success"],
            event_id=result["event_id"],
            wa_id=result["wa_id"],
            detail="WhatsApp notification sent",
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except NotificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
