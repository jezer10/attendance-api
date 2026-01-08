import logging
from datetime import datetime, timezone, tzinfo
from typing import List, Optional

import pytz

from models import AttendanceRequest, AttendanceResponse
from exceptions import NotFoundError, PersistenceError, ValidationError
from services.whatsapp_service import WhatsAppService
from repositories.attendance_repository import AttendanceRepository

logger = logging.getLogger(__name__)


class AttendanceService:
    """Validates attendance schedules and returns deterministic acknowledgements."""

    def __init__(self, repository: Optional[AttendanceRepository] = None) -> None:
        self._repository = repository
        self._whatsapp_service = WhatsAppService()

    def process_attendance(
        self, request: AttendanceRequest, *, current_user: Optional[dict] = None
    ) -> AttendanceResponse:
        """Validate the payload and create a deterministic response."""
        self._validate_request(request)
        self._ensure_user_context(current_user)

        active_windows = self._active_windows(request)
        if not active_windows:
            message = "Attendance schedule saved"
        elif len(active_windows) == 1:
            message = f"{active_windows[0].capitalize()} attendance recorded"
        else:
            message = "Entry and exit attendance recorded"

        response = AttendanceResponse(
            success=True,
            message=message,
            is_active=request.is_active,
            timezone=request.timezone,
            location=request.location,
            schedule=request.schedule,
            phone_number=request.phone_number,
            random_window_minutes=request.random_window_minutes,
            timestamp=datetime.now(),
        )

        self._persist_schedule(request=request, current_user=current_user)
        return response

    @staticmethod
    def _validate_request(request: AttendanceRequest) -> None:
        """Apply minimal sanity checks before acknowledging attendance."""
        if request.location is None:
            raise ValidationError("Location data is required")

        if not request.location.address.strip():
            raise ValidationError("Location address cannot be empty")

        if not request.timezone.strip():
            raise ValidationError("Timezone cannot be empty")

    @staticmethod
    def _active_windows(request: AttendanceRequest) -> List[str]:
        windows = []
        if request.schedule.entry.enabled:
            windows.append("entry")
        if request.schedule.exit.enabled:
            windows.append("exit")
        return windows

    @staticmethod
    def _ensure_user_context(user: Optional[dict]) -> None:
        if not user or not user.get("id"):
            raise ValidationError("Authenticated user context is required")

    def _persist_schedule(
        self, *, request: AttendanceRequest, current_user: Optional[dict]
    ) -> None:
        """Persist the schedule configuration via the repository."""
        user_id = current_user.get("id") if current_user else None
        if not user_id:
            raise ValidationError("Authenticated user context is required")

        recorded_by = current_user.get("id")
        self._get_repository().upsert_schedule(
            user_id=user_id, recorded_by=recorded_by, request=request
        )

    def get_attendance_schedule(
        self, *, current_user: Optional[dict]
    ) -> AttendanceRequest:
        """Retrieve the stored attendance schedule for the authenticated user."""
        self._ensure_user_context(current_user)
        user_id = current_user.get("id")
        try:
            schedule = self._get_repository().fetch_schedule(user_id=user_id)
        except PersistenceError:
            raise

        if schedule is None:
            raise NotFoundError("Attendance schedule not found")

        return schedule

    def get_attendance_schedule_for_user(self, *, user_id: str) -> AttendanceRequest:
        if not user_id:
            raise ValidationError("User id is required")
        try:
            schedule = self._get_repository().fetch_schedule(user_id=user_id)
        except PersistenceError:
            raise
        if schedule is None:
            raise NotFoundError("Attendance schedule not found")
        return schedule

    async def notify_attendance_event(
        self, *, event_id: str, current_user: Optional[dict]
    ) -> dict:
        self._ensure_user_context(current_user)
        user_id = current_user.get("id")

        event = self._get_repository().fetch_event(event_id=event_id)
        if event is None or event.get("user_id") != user_id:
            raise NotFoundError("Attendance event not found")

        schedule = self._get_repository().fetch_schedule(user_id=user_id)
        if schedule is None:
            raise NotFoundError("Attendance schedule not found")

        if not schedule.is_active:
            raise ValidationError("Attendance schedule is inactive")

        if not schedule.phone_number:
            raise ValidationError("Phone number is required to send notifications")

        event_time = self._parse_event_time(event.get("scheduled_for"))
        timezone_name = self._safe_timezone(event.get("timezone") or schedule.timezone)
        local_time = event_time.astimezone(timezone_name)

        response = await self._whatsapp_service.send_template(
            wa_id=self._format_wa_id(schedule.phone_number),
            employee_name=current_user.get("email", "Employee"),
            checkin_date=local_time.strftime("%d/%m/%Y"),
            checkin_time=local_time.strftime("%H:%M"),
            location_address=schedule.location.address,
            location_latitude=float(schedule.location.latitude),
            location_longitude=float(schedule.location.longitude),
        )

        return {
            "success": True,
            "event_id": event_id,
            "wa_id": self._format_wa_id(schedule.phone_number),
            "detail": response,
        }

    @staticmethod
    def _parse_event_time(value: Optional[object]) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if value is None:
            return datetime.now(timezone.utc)
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        raise ValidationError("Invalid event timestamp")

    @staticmethod
    def _safe_timezone(value: str) -> tzinfo:
        parts = value.split()
        for part in reversed(parts):
            if "/" in part:
                try:
                    return pytz.timezone(part)
                except pytz.UnknownTimeZoneError:
                    break
        try:
            return pytz.timezone(value)
        except pytz.UnknownTimeZoneError:
            return timezone.utc

    @staticmethod
    def _format_wa_id(phone_number: str) -> str:
        return phone_number.lstrip("+")

    def _get_repository(self) -> AttendanceRepository:
        if self._repository is None:
            self._repository = AttendanceRepository()
        return self._repository
