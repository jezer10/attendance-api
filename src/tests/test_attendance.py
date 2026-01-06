import pytest
from datetime import time
from dataclasses import dataclass, field

from pydantic import ValidationError as PydanticValidationError

from src.models import (
    AttendanceRequest,
    AttendanceSchedule,
    ScheduleWindow,
    LocationData,
    DayOfWeek,
)
from src.services.attendance_service import AttendanceService
from src.exceptions import NotFoundError, PersistenceError, ValidationError


FAKE_USER = {"id": "user-123", "email": "user@example.com"}


@dataclass
class FakeRepository:
    upsert_should_fail: bool = False
    fetch_should_fail: bool = False
    stored_request: AttendanceRequest | None = None
    calls: list[dict] = field(default_factory=list)

    def upsert_schedule(
        self, *, user_id: str, recorded_by: str, request: AttendanceRequest
    ) -> None:
        if self.upsert_should_fail:
            raise PersistenceError("forced failure")
        self.stored_request = request
        self.calls.append(
            {
                "user_id": user_id,
                "recorded_by": recorded_by,
                "request": request,
            }
        )

    def fetch_schedule(self, *, user_id: str) -> AttendanceRequest | None:
        if self.fetch_should_fail:
            raise PersistenceError("fetch failure")
        return self.stored_request


def make_service(repo: FakeRepository | None = None) -> AttendanceService:
    return AttendanceService(repository=repo or FakeRepository())


def make_request(
    *,
    is_active: bool = True,
    entry_enabled: bool = True,
    exit_enabled: bool = True,
    random_window_minutes: int = 0,
    timezone: str = "UTC-05:00 America/Lima",
) -> AttendanceRequest:
    schedule = AttendanceSchedule(
        entry=ScheduleWindow(
            enabled=entry_enabled,
            local_time=time(8, 5),
            utc_time=time(13, 5),
            days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY],
        ),
        exit=ScheduleWindow(
            enabled=exit_enabled,
            local_time=time(17, 30),
            utc_time=time(22, 30),
            days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY],
        ),
    )
    location = LocationData(
        address="Av. Example 123",
        latitude=-12.04318,
        longitude=-77.02824,
        radius_meters=150,
    )
    return AttendanceRequest(
        is_active=is_active,
        schedule=schedule,
        location=location,
        random_window_minutes=random_window_minutes,
        timezone=timezone,
    )


def test_process_attendance_success_for_entry_and_exit():
    repo = FakeRepository()
    service = make_service(repo)

    response = service.process_attendance(make_request(), current_user=FAKE_USER)

    assert response.success is True
    assert response.message == "Entry and exit attendance recorded"
    assert response.schedule.entry.enabled is True
    assert response.schedule.exit.enabled is True
    assert response.location.address == "Av. Example 123"
    assert repo.calls[0]["user_id"] == FAKE_USER["id"]


def test_process_attendance_single_window_message():
    service = make_service()
    request = make_request(exit_enabled=False)

    response = service.process_attendance(request, current_user=FAKE_USER)

    assert response.message == "Entry attendance recorded"
    assert response.schedule.exit.enabled is False


def test_process_attendance_requires_timezone():
    service = make_service()
    request = make_request(timezone="   ")

    with pytest.raises(ValidationError):
        service.process_attendance(request, current_user=FAKE_USER)


def test_process_attendance_allows_empty_days_for_enabled_window():
    service = make_service()
    schedule = AttendanceSchedule(
        entry=ScheduleWindow(
            enabled=True,
            local_time=time(8, 0),
            utc_time=time(13, 0),
            days=[],
        ),
        exit=ScheduleWindow(
            enabled=False,
            local_time=time(17, 0),
            utc_time=time(22, 0),
            days=[],
        ),
    )
    location = LocationData(
        address="Av. Example 123",
        latitude=-12.04318,
        longitude=-77.02824,
        radius_meters=150,
    )
    request = AttendanceRequest(
        is_active=True,
        schedule=schedule,
        location=location,
        random_window_minutes=0,
        timezone="UTC-05:00 America/Lima",
    )

    response = service.process_attendance(request, current_user=FAKE_USER)

    assert response.message == "Entry attendance recorded"


def test_request_allows_null_times_for_disabled_windows():
    schedule = AttendanceSchedule(
        entry=ScheduleWindow(
            enabled=False,
            local_time=None,
            utc_time=None,
            days=[],
        ),
        exit=ScheduleWindow(
            enabled=False,
            local_time=None,
            utc_time=None,
            days=[],
        ),
    )
    location = LocationData(
        address="Av. Example 123",
        latitude=-12.04318,
        longitude=-77.02824,
        radius_meters=150,
    )

    request = AttendanceRequest(
        is_active=True,
        schedule=schedule,
        location=location,
        random_window_minutes=0,
        timezone="UTC-05:00 America/Lima",
    )

    assert request.schedule.entry.local_time is None
    assert request.schedule.exit.utc_time is None


def test_request_requires_times_when_window_enabled():
    with pytest.raises(PydanticValidationError):
        AttendanceSchedule(
            entry=ScheduleWindow(
                enabled=True,
                local_time=None,
                utc_time=None,
                days=[DayOfWeek.MONDAY],
            ),
            exit=ScheduleWindow(
                enabled=False,
                local_time=None,
                utc_time=None,
                days=[],
            ),
        )


def test_process_attendance_requires_enabled_window():
    service = make_service()
    request = make_request(entry_enabled=False, exit_enabled=False)

    response = service.process_attendance(request, current_user=FAKE_USER)

    assert response.message == "Attendance schedule saved"


def test_process_attendance_propagates_persistence_errors():
    repo = FakeRepository(upsert_should_fail=True)
    service = make_service(repo)

    with pytest.raises(PersistenceError):
        service.process_attendance(make_request(), current_user=FAKE_USER)


def test_get_attendance_schedule_returns_latest_configuration():
    repo = FakeRepository()
    service = make_service(repo)
    request = make_request()
    service.process_attendance(request, current_user=FAKE_USER)

    result = service.get_attendance_schedule(current_user=FAKE_USER)

    assert result == request


def test_get_attendance_schedule_not_found():
    repo = FakeRepository()
    service = make_service(repo)

    with pytest.raises(NotFoundError):
        service.get_attendance_schedule(current_user=FAKE_USER)


def test_get_attendance_schedule_propagates_persistence_errors():
    repo = FakeRepository(fetch_should_fail=True)
    service = make_service(repo)

    with pytest.raises(PersistenceError):
        service.get_attendance_schedule(current_user=FAKE_USER)


def test_process_attendance_requires_user_context():
    service = make_service()

    with pytest.raises(ValidationError):
        service.process_attendance(make_request(), current_user=None)


def test_get_attendance_schedule_requires_user_context():
    service = make_service()

    with pytest.raises(ValidationError):
        service.get_attendance_schedule(current_user=None)
