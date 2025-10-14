from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from httpx import Response

class AttendanceAction(str, Enum):
    ENTRY = "lnk_entrada"
    EXIT = "lnk_salida"

class LocationData(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")

class UserCredentials(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID")
    password: str = Field(..., min_length=1, description="User password")

class AttendanceRequest(BaseModel):
    credentials: UserCredentials
    location: LocationData
    action: AttendanceAction

class AttendanceResponse(BaseModel):
    success: bool
    message: str
    content: Optional[str] = None  # Changed from body to content
    action: AttendanceAction
    timestamp: Optional[datetime] = None
    location: Optional[LocationData] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.now)