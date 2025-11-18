class AttendanceError(Exception):
    """Base exception for attendance API errors."""


class ValidationError(AttendanceError):
    """Raised when data validation fails."""


class PersistenceError(AttendanceError):
    """Raised when persisting data fails."""


class NotFoundError(AttendanceError):
    """Raised when a resource cannot be found."""
