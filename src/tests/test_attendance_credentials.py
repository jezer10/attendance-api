import pytest
from pydantic import ValidationError as PydanticValidationError

from src.models import AttendanceCredentialsGetResponse
from src.models import AttendanceCredentialsRequest
from src.models import AttendanceMarkRequest


def test_credentials_require_non_empty_password():
    with pytest.raises(PydanticValidationError):
        AttendanceCredentialsRequest(companyId=7040, userId=77668171, password="   ")


def test_credentials_accept_valid_payload():
    payload = AttendanceCredentialsRequest(
        companyId=7040, userId=77668171, password="secret"
    )

    assert payload.company_id == 7040
    assert payload.user_id_number == 77668171


def test_mark_request_accepts_entry_and_exit():
    entry_payload = AttendanceMarkRequest(eventType="entry")
    exit_payload = AttendanceMarkRequest(eventType="exit")

    assert entry_payload.event_type == "entry"
    assert exit_payload.event_type == "exit"


def test_credentials_get_response_sets_has_password():
    payload = AttendanceCredentialsGetResponse(
        companyId=7040, userId=77668171, hasPassword=True
    )

    assert payload.company_id == 7040
    assert payload.user_id_number == 77668171
    assert payload.has_password is True
