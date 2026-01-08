from src.models import (
    AttendanceRequest,
    AttendanceResponse,
    AttendanceNotifyRequest,
    AttendanceNotifyResponse,
    AttendanceCredentialsRequest,
    AttendanceCredentialsResponse,
    AttendanceCredentialsGetResponse,
    AttendanceMarkRequest,
    AttendanceMarkResponse,
    AttendanceInternalMarkRequest,
)
from fastapi import HTTPException, Depends, status
from src.services.attendance_service import AttendanceService
from src.services.attendance_credentials_service import AttendanceCredentialsService
from src.services.marking_service import MarkingService
from fastapi import APIRouter
from src.exceptions import (
    NotFoundError,
    PersistenceError,
    ValidationError,
    NotificationError,
    MarkingError,
)
from src.api.deps.auth import get_current_user
from src.api.deps.internal import require_internal_key

import logging

logger = logging.getLogger(__name__)
attendance_service = AttendanceService()
credentials_service = AttendanceCredentialsService()
marking_service = MarkingService()
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


@router.post(
    "/credentials",
    response_model=AttendanceCredentialsResponse,
    response_model_by_alias=True,
)
async def save_attendance_credentials(
    request_body: AttendanceCredentialsRequest,
    current_user: dict = Depends(get_current_user),
) -> AttendanceCredentialsResponse:
    """Persist attendance login credentials for the authenticated user."""
    try:
        credentials_service.save_credentials(
            user_id=current_user.get("id"),
            company_id=request_body.company_id,
            user_id_number=request_body.user_id_number,
            password=request_body.password,
        )
        return AttendanceCredentialsResponse(
            success=True,
            message="Attendance credentials saved",
            company_id=request_body.company_id,
            user_id_number=request_body.user_id_number,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get(
    "/credentials",
    response_model=AttendanceCredentialsGetResponse,
    response_model_by_alias=True,
)
async def get_attendance_credentials(
    current_user: dict = Depends(get_current_user),
) -> AttendanceCredentialsGetResponse:
    """Fetch stored attendance credentials metadata for the authenticated user."""
    try:
        credentials = credentials_service.get_credentials(
            user_id=current_user.get("id")
        )
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance credentials not found",
            )
        return AttendanceCredentialsGetResponse(
            company_id=credentials["company_id"],
            user_id_number=credentials["user_id_number"],
            has_password=bool(credentials.get("password")),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/mark",
    response_model=AttendanceMarkResponse,
    response_model_by_alias=True,
)
async def mark_attendance_event(
    request_body: AttendanceMarkRequest,
    current_user: dict = Depends(get_current_user),
) -> AttendanceMarkResponse:
    """Execute the attendance marking flow."""
    try:
        credentials = credentials_service.get_credentials(
            user_id=current_user.get("id")
        )
        if not credentials or not credentials.get("password"):
            raise ValidationError("Attendance credentials are required")

        schedule = attendance_service.get_attendance_schedule(current_user=current_user)
        location = schedule.location
        if location is None:
            raise ValidationError("Location data is required to mark attendance")

        marking_service.mark_attendance(
            company_id=credentials["company_id"],
            user_id_number=credentials["user_id_number"],
            password=credentials["password"],
            latitude=float(location.latitude),
            longitude=float(location.longitude),
            event_type=request_body.event_type,
        )

        return AttendanceMarkResponse(
            success=True,
            message="Attendance marked",
            event_type=request_body.event_type,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except MarkingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except (NotFoundError, PersistenceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/mark/internal",
    response_model=AttendanceMarkResponse,
    response_model_by_alias=True,
    dependencies=[Depends(require_internal_key)],
)
async def mark_attendance_event_internal(
    request_body: AttendanceInternalMarkRequest,
) -> AttendanceMarkResponse:
    """Execute the attendance marking flow for scheduler calls."""
    try:
        credentials = credentials_service.get_credentials(user_id=request_body.user_id)
        if not credentials or not credentials.get("password"):
            raise ValidationError("Attendance credentials are required")

        schedule = attendance_service.get_attendance_schedule_for_user(
            user_id=request_body.user_id
        )
        location = schedule.location
        if location is None:
            raise ValidationError("Location data is required to mark attendance")

        marking_service.mark_attendance(
            company_id=credentials["company_id"],
            user_id_number=credentials["user_id_number"],
            password=credentials["password"],
            latitude=float(location.latitude),
            longitude=float(location.longitude),
            event_type=request_body.event_type,
        )

        return AttendanceMarkResponse(
            success=True,
            message="Attendance marked",
            event_type=request_body.event_type,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except MarkingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except (NotFoundError, PersistenceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
