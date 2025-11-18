from typing import List, Optional
from enum import Enum
from datetime import datetime, time

from pydantic import BaseModel, Field, PositiveFloat


class DayOfWeek(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class LocationData(BaseModel):
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
    )

    class Config:
        allow_population_by_field_name = True


class ScheduleWindow(BaseModel):
    enabled: bool
    local_time: time = Field()
    utc_time: time = Field()
    days: List[DayOfWeek]

    class Config:
        allow_population_by_field_name = True


class AttendanceSchedule(BaseModel):
    entry: ScheduleWindow
    exit: ScheduleWindow


class AttendanceRequest(BaseModel):
    is_active: bool = Field()
    schedule: AttendanceSchedule
    location: LocationData
    timezone: str

    class Config:
        allow_population_by_field_name = True


class AttendanceResponse(BaseModel):
    success: bool
    message: str
    is_active: bool
    timezone: str
    schedule: AttendanceSchedule
    timestamp: datetime = Field(default_factory=datetime.now)
    location: Optional[LocationData] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.now)
