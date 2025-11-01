class AttendanceError(Exception):
    """Base exception for attendance API errors."""


class ValidationError(AttendanceError):
    """Raised when data validation fails."""
