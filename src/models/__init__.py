from datetime import datetime, time
from enum import Enum
from typing import List, Optional

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
    local_time: time = Field(alias="localTime")
    utc_time: time = Field(alias="utcTime")
    days: List[DayOfWeek]

    @field_validator("days", mode="before")
    @classmethod
    def _remove_null_days(cls, value):
        if isinstance(value, list):
            return [day for day in value if day]
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


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.now)
