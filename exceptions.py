class AttendanceAPIException(Exception):
    """Base exception for attendance API"""
    pass

class AuthenticationError(AttendanceAPIException):
    """Raised when authentication fails"""
    pass

class LocationError(AttendanceAPIException):
    """Raised when location validation fails"""
    pass

class NetworkError(AttendanceAPIException):
    """Raised when network requests fail"""
    pass

class FormParsingError(AttendanceAPIException):
    """Raised when form parsing fails"""
    pass

class ValidationError(AttendanceAPIException):
    """Raised when data validation fails"""
    pass