import pytest

from models import AttendanceRequest, AttendanceAction, LocationData, UserCredentials
from services.attendance_service import AttendanceService
from exceptions import ValidationError


service = AttendanceService()


def make_request(
    user_id: int = 1,
    password: str = "secret",
    action: AttendanceAction = AttendanceAction.ENTRY,
) -> AttendanceRequest:
    return AttendanceRequest(
        credentials=UserCredentials(user_id=user_id, password=password),
        location=LocationData(latitude=0.0, longitude=0.0),
        action=action,
    )


def test_process_attendance_success():
    response = service.process_attendance(make_request())

    assert response.success is True
    assert response.message == "Entry marked successfully"
    assert response.action == AttendanceAction.ENTRY
    assert response.location.latitude == 0.0


def test_process_attendance_requires_password():
    request = make_request(password="   ")

    with pytest.raises(ValidationError):
        service.process_attendance(request)
