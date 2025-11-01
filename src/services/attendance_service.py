import logging
from datetime import datetime

from models import AttendanceRequest, AttendanceResponse, AttendanceAction
from exceptions import ValidationError

logger = logging.getLogger(__name__)


class AttendanceService:
    """Lightweight domain service that validates and records attendance events."""

    def __init__(self) -> None:
        self._messages = {
            AttendanceAction.ENTRY: "Entry marked successfully",
            AttendanceAction.EXIT: "Exit marked successfully",
        }

    def process_attendance(self, request: AttendanceRequest) -> AttendanceResponse:
        """Validate the payload and create a deterministic response."""
        logger.info("Recording %s for user %s", request.action, request.credentials.user_id)
        self._validate_request(request)

        message = self._messages[request.action]
        return AttendanceResponse(
            success=True,
            message=message,
            action=request.action,
            timestamp=datetime.now(),
            location=request.location,
        )

    @staticmethod
    def _validate_request(request: AttendanceRequest) -> None:
        """Apply minimal sanity checks before acknowledging attendance."""
        if not request.credentials.password.strip():
            raise ValidationError("Password cannot be empty")

        if request.location is None:
            raise ValidationError("Location data is required")
