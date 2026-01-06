from datetime import datetime, time
from enum import Enum
from typing import List, Optional, Literal

import re

from pydantic import BaseModel, Field, PositiveFloat, ConfigDict, field_validator


class DayOfWeek(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class LocationData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address: str = Field(..., min_length=1, description="Street address or landmark")
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude in decimal degrees"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude in decimal degrees"
    )
    radius_meters: PositiveFloat = Field(
        ...,
        description="Allowed radius in meters for attendance validation",
        alias="radiusMeters",
    )


class ScheduleWindow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool
    local_time: Optional[time] = Field(alias="localTime", default=None)
    utc_time: Optional[time] = Field(alias="utcTime", default=None)
    days: List[DayOfWeek]

    @field_validator("days", mode="before")
    @classmethod
    def _remove_null_days(cls, value):
        if isinstance(value, list):
            return [day for day in value if day]
        return value

    @field_validator("local_time", "utc_time")
    @classmethod
    def _require_time_when_enabled(cls, value, info):
        if value is None and info.data.get("enabled"):
            raise ValueError(f"{info.field_name} is required when enabled is true")
        return value


class AttendanceSchedule(BaseModel):
    entry: ScheduleWindow
    exit: ScheduleWindow


class AttendanceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    is_active: bool = Field(alias="isActive")
    schedule: AttendanceSchedule
    location: LocationData
    phone_number: Optional[str] = Field(alias="phoneNumber", default=None)
    random_window_minutes: int = Field(
        0,
        alias="randomWindowMinutes",
        ge=0,
        le=240,
        description="Random window minutes around the scheduled time",
    )
    timezone: str

    @field_validator("phone_number")
    @classmethod
    def _validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        if not re.fullmatch(r"\+[1-9]\d{1,14}", trimmed):
            raise ValueError("Phone number must be in E.164 format")
        return trimmed

    @field_validator("schedule")
    @classmethod
    def _validate_schedule_order(cls, value: AttendanceSchedule) -> AttendanceSchedule:
        if value.entry.enabled and value.exit.enabled:
            if (
                value.entry.local_time is not None
                and value.exit.local_time is not None
                and value.exit.local_time <= value.entry.local_time
            ):
                raise ValueError(
                    "Exit time must be later than entry time on the same day"
                )
        return value


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    is_active: bool = Field(alias="isActive")
    timezone: str
    schedule: AttendanceSchedule
    phone_number: Optional[str] = Field(alias="phoneNumber", default=None)
    random_window_minutes: int = Field(alias="randomWindowMinutes")
    timestamp: datetime = Field(default_factory=datetime.now)
    location: Optional[LocationData] = None


class AttendanceNotifyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(alias="eventId")


class AttendanceNotifyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    event_id: str = Field(alias="eventId")
    wa_id: str = Field(alias="waId")
    detail: str


class AttendanceMarkRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_type: Literal["entry", "exit"] = Field(alias="eventType")


class AttendanceMarkResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    event_type: Literal["entry", "exit"] = Field(alias="eventType")
    timestamp: datetime = Field(default_factory=datetime.now)


class AttendanceInternalMarkRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_type: Literal["entry", "exit"] = Field(alias="eventType")
    user_id: str = Field(alias="userId", min_length=1)


class AttendanceCredentialsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company_id: int = Field(alias="companyId", ge=1)
    user_id_number: int = Field(alias="userId", ge=1)
    password: str = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Password cannot be empty")
        return trimmed


class AttendanceCredentialsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    company_id: int = Field(alias="companyId")
    user_id_number: int = Field(alias="userId")


class AttendanceCredentialsGetResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company_id: int = Field(alias="companyId")
    user_id_number: int = Field(alias="userId")
    has_password: bool = Field(alias="hasPassword")


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.now)
