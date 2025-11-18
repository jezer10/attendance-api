import logging
from datetime import datetime
from typing import List, Optional

from src.models import AttendanceRequest, AttendanceResponse, ScheduleWindow
from src.exceptions import NotFoundError, PersistenceError, ValidationError
from src.services.attendance_repository import AttendanceRepository

logger = logging.getLogger(__name__)


class AttendanceService:
    """Validates attendance schedules and returns deterministic acknowledgements."""

    def __init__(self, repository: Optional[AttendanceRepository] = None) -> None:
        self._repository = repository

    def process_attendance(
        self, request: AttendanceRequest, *, current_user: Optional[dict] = None
    ) -> AttendanceResponse:
        """Validate the payload and create a deterministic response."""
        self._validate_request(request)
        self._ensure_user_context(current_user)

        active_windows = self._active_windows(request)
        if len(active_windows) == 1:
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

        AttendanceService._validate_window(request.schedule.entry, "entry")
        AttendanceService._validate_window(request.schedule.exit, "exit")

        if not any(w.enabled for w in (request.schedule.entry, request.schedule.exit)):
            raise ValidationError("At least one schedule window must be enabled")

    @staticmethod
    def _validate_window(window: ScheduleWindow, label: str) -> None:
        if window.enabled and not window.days:
            raise ValidationError(f"{label.capitalize()} schedule must include days")

    @staticmethod
    def _active_windows(request: AttendanceRequest) -> List[str]:
        windows = []
        if request.schedule.entry.enabled:
            windows.append("entry")
        if request.schedule.exit.enabled:
            windows.append("exit")
        return windows or ["entry"]

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

    def _get_repository(self) -> AttendanceRepository:
        if self._repository is None:
            self._repository = AttendanceRepository()
        return self._repository
